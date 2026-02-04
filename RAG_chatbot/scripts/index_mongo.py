"""Script to build knowledge base from MongoDB posts and comments."""

import sys
from pathlib import Path
from typing import Any, Dict, List

from pymongo import MongoClient

# Thêm thư mục gốc vào Python path để có thể import src
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.utils.config import MONGO_DB_NAME, MONGO_DB_SOURCE, get_mongo_client


def build_knowledge_documents() -> int:
    """
    Build knowledge base from MongoDB posts and comments.
    
    Đọc posts và comments từ database 'Postandcmt'
    Ghi knowledge_base vào database 'Chatbot'
    
    Normalizes posts and comments into a unified format for RAG.
    """
    client = get_mongo_client()
    
    # Đọc dữ liệu nguồn từ database Postandcmt
    source_db = client[MONGO_DB_SOURCE]
    posts_col = source_db["posts"]
    comments_col = source_db["comments"]
    
    # Ghi knowledge_base vào database Chatbot
    target_db = client[MONGO_DB_NAME]
    kb_col = target_db["knowledge_base"]

    kb_col.delete_many({})

    documents: List[Dict[str, Any]] = []

    for post in posts_col.find():
        post_id = str(post.get("_id"))
        message = (post.get("message") or "").strip()
        if not message:
            message = "[NO_MESSAGE]"

        doc = {
            "_id": f"post::{post_id}",
            "type": "post",
            "text": message,
            "source": {
                "post_id": post_id,
                "permalink_url": post.get("permalink_url"),
            },
            "created_time": post.get("created_time"),
            "fetched_at": post.get("fetched_at"),
        }
        documents.append(doc)

    for cmt in comments_col.find():
        comment_id = str(cmt.get("_id"))
        message = (cmt.get("message") or "").strip()
        if not message:
            message = "[NO_MESSAGE]"

        doc = {
            "_id": f"comment::{comment_id}",
            "type": "comment",
            "text": message,
            "source": {
                "post_id": cmt.get("post_id"),
                "comment_id": comment_id,
                "permalink_url": cmt.get("permalink_url"),
            },
            "created_time": cmt.get("created_time"),
            "fetched_at": cmt.get("fetched_at"),
        }
        documents.append(doc)

    if not documents:
        print("No posts/comments found in MongoDB.")
        return 0

    kb_col.insert_many(documents, ordered=False)
    print(f"Inserted {len(documents)} documents into 'knowledge_base' collection.")
    return len(documents)


if __name__ == "__main__":
    build_knowledge_documents()

