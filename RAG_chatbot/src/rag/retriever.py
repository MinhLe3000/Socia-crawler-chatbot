"""RAG retriever implementation using BGE-M3 with hybrid search."""

import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from FlagEmbedding import BGEM3FlagModel
from src.utils.config import get_qdrant_client, QDRANT_COLLECTION_NAME


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Calculate cosine similarity between vectors."""
    if a.ndim == 1:
        a = a[None, :]
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8)
    return np.dot(a_norm, b_norm.T)


def _sparse_sim(query_sparse: Dict[int, float], doc_sparse: Dict[int, float]) -> float:
    """Calculate sparse similarity (BM25-like) between query and document."""
    if not query_sparse or not doc_sparse:
        return 0.0
    score = 0.0
    for token_id, weight in query_sparse.items():
        doc_weight = doc_sparse.get(token_id)
        if doc_weight is not None:
            score += weight * doc_weight
    return float(score)


def _is_nonzero_vector(vec: Any) -> bool:
    """Return True if vec is a valid dense vector and not all zeros."""
    if vec is None:
        return False
    if not isinstance(vec, (list, tuple, np.ndarray)):
        return False
    arr = np.asarray(vec, dtype=np.float32)
    if arr.size == 0:
        return False
    return bool(np.any(np.abs(arr) > 1e-12))


# Types used for retrieval (post + comment_context + thread_summary để match câu hỏi kiểu "review thầy X")
RETRIEVAL_TYPES = ["post", "comment_context", "thread_summary"]


def _extract_quoted_phrases(query: str) -> List[str]:
    """Lấy các cụm trong ngoặc kép từ query (exact phrase)."""
    return [m.strip().lower() for m in re.findall(r'"([^"]+)"', query) if m.strip()]


class RAGRetriever:
    """
    RAG retriever using BGE-M3 with hybrid search (dense + sparse).

    - Retrieval: post, comment_context, thread_summary (để match nội dung review trong comment/thread).
    - Comments (type=comment) chỉ dùng để enrich context sau khi đã chọn post.
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        top_k: int = 5,
        min_score: Optional[float] = None,
        use_hybrid: bool = True,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        comment_limit: int = 8,
        model_name: str = "BAAI/bge-m3",
        use_fp16: bool = True,
    ) -> None:
        self.collection_name = collection_name or QDRANT_COLLECTION_NAME
        self.top_k = top_k
        self.min_score = min_score
        self.use_hybrid = use_hybrid
        self.comment_limit = comment_limit

        total_weight = dense_weight + sparse_weight
        if total_weight <= 0:
            self.dense_weight = 0.7
            self.sparse_weight = 0.3
        else:
            self.dense_weight = dense_weight / total_weight
            self.sparse_weight = sparse_weight / total_weight

        self.qdrant_client = get_qdrant_client()
        self.model = BGEM3FlagModel(model_name, use_fp16=use_fp16)

        self._load_embeddings_cache()
        self._load_comments_cache()

    def _scroll_all_points(
        self,
        with_payload: bool = True,
        with_vectors: bool = False,
        batch_size: int = 1000,
    ) -> List[Any]:
        """Scroll all points from Qdrant with pagination (no payload filter — Qdrant Cloud cần index)."""
        all_points: List[Any] = []
        offset = None
        while True:
            points, offset = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=batch_size,
                with_payload=with_payload,
                with_vectors=with_vectors,
                offset=offset,
            )
            if not points:
                break
            all_points.extend(points)
            if offset is None:
                break
        return all_points

    def _load_embeddings_cache(self) -> None:
        """Load embeddings for retrieval (post + comment_context + thread_summary) into RAM."""
        points = self._scroll_all_points(with_payload=True, with_vectors=True)

        if not points:
            raise RuntimeError(
                f"No points found in Qdrant collection '{self.collection_name}'. "
                "Run scripts/index_mongo.py and scripts/embed_bge_m3.py first."
            )

        valid_points = []
        for p in points:
            payload = p.payload or {}
            if payload.get("type") not in RETRIEVAL_TYPES:
                continue
            if not _is_nonzero_vector(p.vector):
                continue
            valid_points.append(p)

        if not valid_points:
            raise RuntimeError(
                f"Found {len(points)} points but none have valid embeddings. "
                "Run scripts/embed_bge_m3.py to generate embeddings."
            )

        self.point_ids = [int(p.id) for p in valid_points]
        self.doc_ids = [str((p.payload or {}).get("doc_id", "")) for p in valid_points]
        self.doc_texts = [str((p.payload or {}).get("text", "")) for p in valid_points]
        self.doc_sources = [dict((p.payload or {}).get("source", {}) or {}) for p in valid_points]

        emb_list = [np.asarray(p.vector, dtype=np.float32) for p in valid_points]
        self.embeddings = np.stack(emb_list, axis=0)

        self.sparse_embeddings: List[Dict[int, float]] = []
        if self.use_hybrid:
            for p in valid_points:
                sparse = (p.payload or {}).get("sparse_embedding")
                if isinstance(sparse, dict) and sparse:
                    cleaned = {}
                    for k, v in sparse.items():
                        try:
                            cleaned[int(k)] = float(v)
                        except (TypeError, ValueError):
                            continue
                    self.sparse_embeddings.append(cleaned)
                else:
                    self.sparse_embeddings.append({})

        print("RAGRetriever v2 loaded.")
        print(f"  Collection: {self.collection_name}")
        print(f"  Retrieval points: {len(self.doc_ids)} (post + comment_context + thread_summary)")
        print(f"  Dense: {len(self.embeddings)}")
        if self.use_hybrid:
            n = sum(1 for s in self.sparse_embeddings if s)
            print(f"  Sparse: {n}/{len(self.sparse_embeddings)}")

    def _load_comments_cache(self) -> None:
        """Load comments by post_id from Qdrant (lọc type=comment trong Python)."""
        points = self._scroll_all_points(with_payload=True, with_vectors=False)

        self.comments_by_post: Dict[str, List[Dict[str, Any]]] = {}
        for point in points:
            payload = point.payload or {}
            source = payload.get("source", {}) or {}
            if payload.get("type") != "comment":
                continue
            post_id = source.get("post_id")
            if not post_id:
                continue
            self.comments_by_post.setdefault(str(post_id), []).append({
                "text": str(payload.get("text", "")).strip(),
                "comment_id": source.get("comment_id"),
                "created_time": payload.get("created_time"),
            })

        total = sum(len(v) for v in self.comments_by_post.values())
        print(f"Loaded {total} comments for {len(self.comments_by_post)} posts.")

    def _encode_query(self, query: str) -> Tuple[np.ndarray, Optional[Dict[int, float]]]:
        """Encode query into dense and optional sparse."""
        outputs = self.model.encode(
            [query],
            return_dense=True,
            return_sparse=self.use_hybrid,
            return_colbert_vecs=False,
        )
        q_vec = np.asarray(outputs["dense_vecs"][0], dtype=np.float32)
        q_sparse = None
        if self.use_hybrid and outputs.get("sparse_vecs"):
            raw = outputs["sparse_vecs"][0]
            if isinstance(raw, dict):
                q_sparse = {}
                for k, v in raw.items():
                    try:
                        q_sparse[int(k)] = float(v)
                    except (TypeError, ValueError):
                        continue
        return q_vec, q_sparse

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant docs; dedup by post_id/permalink_url."""
        if top_k is None:
            top_k = self.top_k
        if not query or not query.strip():
            return []

        q_vec, q_sparse = self._encode_query(query)
        dense_sims = _cosine_sim(q_vec, self.embeddings)[0]
        dense_norm = (dense_sims + 1.0) / 2.0

        if self.use_hybrid and q_sparse is not None and self.sparse_embeddings:
            sparse_sims = np.array(
                [_sparse_sim(q_sparse, s) for s in self.sparse_embeddings],
                dtype=np.float32,
            )
            if sparse_sims.size > 0 and sparse_sims.max() > sparse_sims.min():
                sparse_sims = (sparse_sims - sparse_sims.min()) / (sparse_sims.max() - sparse_sims.min() + 1e-8)
            else:
                sparse_sims = np.zeros_like(sparse_sims, dtype=np.float32)
            final_scores = self.dense_weight * dense_norm + self.sparse_weight * sparse_sims
        else:
            final_scores = np.array(dense_norm, dtype=np.float32, copy=True)

        # Exact phrase boost: query có cụm trong ngoặc kép "..." thì tăng điểm doc chứa đúng cụm đó
        quoted_phrases = _extract_quoted_phrases(query)
        if quoted_phrases:
            for i, text in enumerate(self.doc_texts):
                text_lower = (text or "").lower()
                if all(phrase in text_lower for phrase in quoted_phrases):
                    final_scores[i] += 0.35
            final_scores = np.clip(final_scores, 0.0, 1.5)

        if self.min_score is not None:
            valid = np.where(final_scores >= self.min_score)[0]
            if len(valid) == 0:
                sorted_idx = np.argsort(-final_scores)
            else:
                sorted_idx = valid[np.argsort(-final_scores[valid])]
        else:
            sorted_idx = np.argsort(-final_scores)

        seen_keys: set = set()
        results: List[Dict[str, Any]] = []
        for idx in sorted_idx:
            src = self.doc_sources[idx] or {}
            dedup_key = src.get("post_id") or src.get("permalink_url") or self.doc_ids[idx]
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)
            results.append({
                "_id": self.doc_ids[idx],
                "score": float(final_scores[idx]),
                "dense_score": float(dense_sims[idx]),
                "text": self.doc_texts[idx],
                "source": src,
            })
            if len(results) >= top_k:
                break
        return results

    def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get post by post_id from cache or Qdrant."""
        doc_id = f"post::{post_id}"
        try:
            idx = self.doc_ids.index(doc_id)
            return {
                "_id": self.doc_ids[idx],
                "text": self.doc_texts[idx],
                "source": self.doc_sources[idx],
                "score": 1.0,
            }
        except ValueError:
            pass

        # Scroll và tìm post theo doc_id (không dùng filter vì Qdrant Cloud cần payload index)
        all_points = self._scroll_all_points(with_payload=True, with_vectors=False, batch_size=500)
        for p in all_points:
            payload = p.payload or {}
            if payload.get("type") == "post" and payload.get("doc_id") == doc_id:
                return {
                    "_id": str(payload.get("doc_id", "")),
                    "text": str(payload.get("text", "")),
                    "source": dict(payload.get("source", {}) or {}),
                    "score": 1.0,
                }
        return None


def build_context(retrieved_docs: List[Dict[str, Any]]) -> str:
    """Format retrieved documents into context string for LLM."""
    parts = []
    for i, d in enumerate(retrieved_docs, start=1):
        meta = d.get("source", {}) or {}
        link = meta.get("permalink_url") or ""
        ds = d.get("dense_score")
        if ds is not None:
            parts.append(
                f"[DOC {i}] score={d['score']:.3f} (dense={ds:.3f})\n"
                f"text: {d.get('text', '')}\nsource: {link}\n"
            )
        else:
            parts.append(
                f"[DOC {i}] score={d['score']:.3f}\ntext: {d.get('text', '')}\nsource: {link}\n"
            )
    return "\n\n".join(parts)


def build_single_context(doc: Dict[str, Any], retriever: Optional["RAGRetriever"] = None) -> str:
    """Format one post and limited comments for LLM."""
    meta = doc.get("source", {}) or {}
    link = meta.get("permalink_url") or ""
    post_id = meta.get("post_id")

    context_parts = [
        "=== BAI VIET ===",
        f"text: {doc.get('text', '')}",
        f"source: {link}",
    ]

    if retriever and post_id and hasattr(retriever, "comments_by_post"):
        comments = retriever.comments_by_post.get(post_id, [])
        comments = [c for c in comments if c.get("text") and c.get("text") != "[NO_MESSAGE]"]
        limit = getattr(retriever, "comment_limit", 8)
        if comments:
            context_parts.append("\n=== COMMENTS ===")
            for cmt in comments[:limit]:
                text = cmt.get("text", "").strip()
                snippet = text[:60] + "..." if len(text) > 60 else text
                context_parts.append(f"Bình luận ({snippet}): {text}")
            if len(comments) > limit:
                context_parts.append(f"[GHI CHÚ] Còn {len(comments) - limit} bình luận khác không đưa vào context.")

    return "\n".join(context_parts)


def build_prompt(user_question: str, context: str) -> str:
    """Build prompt for LLM."""
    return (
        "Bạn là trợ lý AI thân thiện của nhóm sinh viên, giúp tóm tắt và trả lời câu hỏi "
        "dựa trên các bài đăng và bình luận trong nhóm.\n\n"
        "NHIỆM VỤ:\n"
        "1. Đọc kỹ tài liệu trong CONTEXT.\n"
        "2. Ưu tiên thông tin từ bài viết gốc, sau đó mới dùng bình luận liên quan cùng bài.\n"
        "3. Nếu có ý kiến trái chiều, trình bày cân bằng.\n"
        "4. Trả lời ngắn gọn, rõ ràng, thân thiện.\n\n"
        "QUY TẮC:\n"
        "- CHỈ dùng thông tin có trong CONTEXT.\n"
        "- Không bịa, không suy đoán.\n"
        '- Khi nhắc đến bình luận, viết tự nhiên: "một bình luận cho biết..." hoặc "một ý kiến khác nói rằng...".\n'
        '- Dùng "[Bài viết]" khi nói về nội dung chính của post.\n'
        '- Nếu CONTEXT không đủ thông tin, trả lời: '
        '"Mình không thấy thông tin về vấn đề này trong nhóm. Bạn có thể hỏi cụ thể hơn không?"\n\n'
        f"=== CONTEXT ===\n{context}\n\n"
        f"=== CÂU HỎI ===\n{user_question}\n\n"
        "=== TRẢ LỜI ===\n"
    )
