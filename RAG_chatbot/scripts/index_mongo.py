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

    for post in posts_col.find():
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

    for cmt in comments_col.find():
        comment_id = str(cmt.get("_id"))
        message = (cmt.get("message") or "").strip()
        if not message:
            message = "[NO_MESSAGE]"

        payload = {
            "doc_id": f"comment::{comment_id}",
            "type": "comment",
            "text": message,
            "source": {
                "post_id": cmt.get("post_id"),
                "comment_id": comment_id,
                "permalink_url": cmt.get("permalink_url"),
            },
            "created_time": str(cmt.get("created_time")) if cmt.get("created_time") else None,
            "fetched_at": str(cmt.get("fetched_at")) if cmt.get("fetched_at") else None,
        }
        
        zero_vector = np.zeros(1024, dtype=np.float32).tolist()
        
        points.append(
            PointStruct(
                id=point_id,
                vector=zero_vector,
                payload=payload,
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

