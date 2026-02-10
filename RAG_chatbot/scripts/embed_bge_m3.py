"""Script to generate embeddings for knowledge base using BGE-M3 model."""

from typing import List
import numpy as np
from FlagEmbedding import BGEM3FlagModel
from qdrant_client.http.models import PointStruct

from config import QDRANT_COLLECTION_NAME, get_qdrant_client


def embed_knowledge_base(
    batch_size: int = 16,
    collection_name: str = None,
    use_sparse: bool = False,  # Qdrant free tier không hỗ trợ sparse vectors tốt
) -> int:
    """
    Generate embeddings for knowledge base using BGE-M3 model.
    
    Reads from Qdrant, generates embeddings, and updates vectors.
    """
    if collection_name is None:
        collection_name = QDRANT_COLLECTION_NAME
        
    qdrant_client = get_qdrant_client()
    model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)

    # Scroll through all points in Qdrant
    points, _ = qdrant_client.scroll(
        collection_name=collection_name,
        limit=10000,  # Lấy tối đa 10k points
        with_payload=True,
        with_vectors=True,
    )
    
    if not points:
        print(f"No documents found in Qdrant collection '{collection_name}'. Please run index_mongo.py first.")
        return 0

    total = len(points)
    print(f"Starting embedding generation for {total} documents using BGE-M3...")
    print("  - Dense embeddings: ON")
    if use_sparse:
        print("  - Sparse embeddings: ON (hybrid search)")

    updated = 0
    updated_points: List[PointStruct] = []
    
    for i in range(0, total, batch_size):
        batch = points[i : i + batch_size]
        texts: List[str] = [str(p.payload.get("text", "")) for p in batch]

        outputs = model.encode(
            texts,
            return_dense=True,
            return_sparse=use_sparse,
            return_colbert_vecs=False,
        )
        dense_vectors = outputs["dense_vecs"]
        sparse_vectors = outputs.get("sparse_vecs", []) if use_sparse else []

        for idx, (point, vec) in enumerate(zip(batch, dense_vectors)):
            # Convert to float32 to reduce storage size
            vec32 = np.asarray(vec, dtype=np.float32).tolist()
            
            # Update payload với thông tin embedding
            updated_payload = dict(point.payload)
            updated_payload["embedding_model"] = "BAAI/bge-m3"
            updated_payload["embedding_dim"] = len(vec32)
            
            if use_sparse and sparse_vectors:
                sparse_dict = sparse_vectors[idx]
                sparse_dict_clean = {int(k): float(v) for k, v in sparse_dict.items()}
                updated_payload["sparse_embedding"] = sparse_dict_clean
            
            # Tạo point mới với vector đã embed
            updated_points.append(
                PointStruct(
                    id=point.id,
                    vector=vec32,
                    payload=updated_payload,
                )
            )
            updated += 1

        print(f"Processed {min(i + batch_size, total)}/{total} documents")

    # Upload tất cả points đã cập nhật vào Qdrant
    if updated_points:
        qdrant_client.upsert(
            collection_name=collection_name,
            points=updated_points,
            wait=True,
        )
    
    print(f"Hoan thanh. Da cap nhat embedding cho {updated} documents trong Qdrant.")
    return updated


if __name__ == "__main__":
    embed_knowledge_base()

