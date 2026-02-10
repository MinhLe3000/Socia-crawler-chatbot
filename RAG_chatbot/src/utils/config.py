"""Configuration settings for MongoDB and Qdrant connections."""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from qdrant_client import QdrantClient

load_dotenv()

# MongoDB Connection URI
MONGO_URI = "mongodb+srv://mle333999_db:LGWX15KzZEZSXxRS@deandatabase.uuskv7o.mongodb.net/?appName=Deandatabase"

# Database names
# Database chứa posts và comments (đọc dữ liệu nguồn)
MONGO_DB_SOURCE = "Postandcmt"  # Database chứa posts và comments

# Database chứa chatlogs (ghi dữ liệu RAG)
MONGO_DB_NAME = "Chatbot"  # Database chứa chatlogs

# Qdrant Configuration
QDRANT_URL = os.getenv(
    "QDRANT_URL", 
    "your_qdrant_url_here"  
)
QDRANT_KEY = os.getenv("QDRANT_KEY")
QDRANT_COLLECTION_NAME = "knowledge_base"


def get_mongo_client() -> MongoClient:
    """Get MongoDB client instance."""
    return MongoClient(MONGO_URI)


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance."""
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_KEY,
    )

