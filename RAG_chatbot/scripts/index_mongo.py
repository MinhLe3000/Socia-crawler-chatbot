"""Script to build knowledge base from MongoDB posts and comments."""

from typing import Any, Dict, List
import numpy as np
from pymongo import MongoClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

from config import (
    MONGO_DB_SOURCE,
    QDRANT_COLLECTION_NAME,
    get_mongo_client,
    get_qdrant_client,
)


def build_knowledge_documents() -> int:
    """
    Build knowledge base from MongoDB posts and comments.
    
    Reads posts and comments from the source DB configured in .env
    (MONGO_DB_SOURCE) and stores them into the Qdrant collection.
    """
    mongo_client = get_mongo_client()
    qdrant_client = get_qdrant_client()
    
    source_db = mongo_client[MONGO_DB_SOURCE]
    posts_col = source_db["posts"]
    comments_col = source_db["comments"]

    # Cache all posts in memory so we can reuse both for
    # - indexing post documents
    # - building comment_context (need post.message)
    posts = list(posts_col.find())

    # Map post_id -> post_message (cleaned)
    post_messages = {}
    for post in posts:
        pid = str(post.get("_id"))
        msg = (post.get("message") or "").strip()
        if msg:
            post_messages[pid] = msg

    # post_id -> list of comment texts (chỉ comment đủ dài, để build thread_summary)
    comments_by_post: Dict[str, List[str]] = {}
    for cmt in comments_col.find():
        post_id_str = str(cmt.get("post_id")) if cmt.get("post_id") else None
        if not post_id_str:
            continue
        raw = (cmt.get("message") or "").strip()
        if raw and len(raw) > 10:
            if post_id_str not in comments_by_post:
                comments_by_post[post_id_str] = []
            comments_by_post[post_id_str].append(raw)
    
    # Tạo Qdrant collection nếu chưa tồn tại
    # BGE-M3 model có 1024 dimensions
    collections = qdrant_client.get_collections().collections
    collection_exists = any(c.name == QDRANT_COLLECTION_NAME for c in collections)
    
    if not collection_exists:
        qdrant_client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=1024,  # BGE-M3 embedding dimension
                distance=Distance.COSINE,
            ),
        )
        print(f"Created Qdrant collection '{QDRANT_COLLECTION_NAME}'")
    else:
        # Xóa tất cả points cũ nếu collection đã tồn tại
        try:
            qdrant_client.delete_collection(QDRANT_COLLECTION_NAME)
            qdrant_client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=1024,
                    distance=Distance.COSINE,
                ),
            )
            print(f"Recreated Qdrant collection '{QDRANT_COLLECTION_NAME}'")
        except Exception as e:
            print(f"Warning: Could not recreate collection: {e}")

    # Chuẩn bị danh sách points cho Qdrant
    points: List[PointStruct] = []
    point_id = 0

    # ============================
    # Index posts
    # ============================
    for post in posts:
        post_id = str(post.get("_id"))
        message = (post.get("message") or "").strip()
        if not message:
            message = "[NO_MESSAGE]"

        payload = {
            "doc_id": f"post::{post_id}",
            "type": "post",
            "text": message,
            "source": {
                "post_id": post_id,
                "permalink_url": post.get("permalink_url"),
                "thread_id": post_id,
            },
            "created_time": str(post.get("created_time")) if post.get("created_time") else None,
            "fetched_at": str(post.get("fetched_at")) if post.get("fetched_at") else None,
        }

        # Tạo zero vector tạm thời (sẽ được update bởi embed_bge_m3.py)
        zero_vector = np.zeros(1024, dtype=np.float32).tolist()

        points.append(
            PointStruct(
                id=point_id,
                vector=zero_vector,
                payload=payload,
            )
        )
        point_id += 1

    # ============================
    # Index comments + comment_context
    # ============================
    for cmt in comments_col.find():
        comment_id = str(cmt.get("_id"))
        raw_message = (cmt.get("message") or "").strip()
        message = raw_message if raw_message else "[NO_MESSAGE]"

        post_id = cmt.get("post_id")
        post_id_str = str(post_id) if post_id is not None else None

        # Base comment document (giữ nguyên để build COMMENTS context)
        payload_comment = {
            "doc_id": f"comment::{comment_id}",
            "type": "comment",
            "text": message,
            "source": {
                "post_id": post_id_str,
                "comment_id": comment_id,
                "permalink_url": cmt.get("permalink_url"),
                "thread_id": post_id_str,
            },
            "created_time": str(cmt.get("created_time")) if cmt.get("created_time") else None,
            "fetched_at": str(cmt.get("fetched_at")) if cmt.get("fetched_at") else None,
        }

        zero_vector = np.zeros(1024, dtype=np.float32).tolist()

        points.append(
            PointStruct(
                id=point_id,
                vector=zero_vector,
                payload=payload_comment,
            )
        )
        point_id += 1

        # Comment_context document: Bài viết + Bình luận (chỉ với comment đủ dài)
        post_message = post_messages.get(post_id_str, "")
        if raw_message and len(raw_message) > 10 and post_message:
            text_context = f"Bài viết: {post_message}\nBình luận: {raw_message}"

            payload_comment_context = {
                "doc_id": f"comment_context::{comment_id}",
                "type": "comment_context",
                "text": text_context,
                "source": {
                    "post_id": post_id_str,
                    "comment_id": comment_id,
                    "permalink_url": cmt.get("permalink_url"),
                    "thread_id": post_id_str,
                },
                "created_time": str(cmt.get("created_time")) if cmt.get("created_time") else None,
                "fetched_at": str(cmt.get("fetched_at")) if cmt.get("fetched_at") else None,
            }

            points.append(
                PointStruct(
                    id=point_id,
                    vector=zero_vector,
                    payload=payload_comment_context,
                )
            )
            point_id += 1

    # ============================
    # Index thread_summary (1 doc/thread: post + các ý chính từ comment)
    # ============================
    for post in posts:
        post_id = str(post.get("_id"))
        post_message = post_messages.get(post_id, "").strip() or "[NO_MESSAGE]"
        comment_texts = comments_by_post.get(post_id, [])

        lines = [f"Thread: {post_message}"]
        if comment_texts:
            lines.append("Các ý chính từ bình luận:")
            for c in comment_texts:
                lines.append(f"- {c}")
        else:
            lines.append("Các ý chính từ bình luận: (chưa có)")

        text_summary = "\n".join(lines)

        payload_thread = {
            "doc_id": f"thread_summary::{post_id}",
            "type": "thread_summary",
            "text": text_summary,
            "source": {
                "post_id": post_id,
                "permalink_url": post.get("permalink_url"),
                "thread_id": post_id,
            },
            "created_time": str(post.get("created_time")) if post.get("created_time") else None,
            "fetched_at": str(post.get("fetched_at")) if post.get("fetched_at") else None,
        }

        zero_vector = np.zeros(1024, dtype=np.float32).tolist()
        points.append(
            PointStruct(
                id=point_id,
                vector=zero_vector,
                payload=payload_thread,
            )
        )
        point_id += 1

    if not points:
        print("No posts/comments found in MongoDB.")
        return 0

    # Upload points vào Qdrant
    qdrant_client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=points,
        wait=True,
    )
    
    print(f"Inserted {len(points)} documents into Qdrant collection '{QDRANT_COLLECTION_NAME}'.")
    print("Note: Vectors are initialized as zeros. Run embed_bge_m3.py to generate actual embeddings.")
    return len(points)


if __name__ == "__main__":
    build_knowledge_documents()

