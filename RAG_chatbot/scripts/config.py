"""Configuration for MongoDB and Qdrant connections."""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from qdrant_client import QdrantClient

load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_SOURCE = "chatbotNeu"  # Database chứa posts và comments
MONGO_DB_NAME = "chatbotNeu"  # Database chatbot

# Qdrant Configuration
QDRANT_URL = os.getenv(
    "QDRANT_URL"
)
QDRANT_KEY = os.getenv("QDRANT_KEY")
QDRANT_COLLECTION_NAME = "knowledge_base"


def get_mongo_client() -> MongoClient:
    """Get MongoDB client."""
    return MongoClient(MONGO_URI)


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client."""
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_KEY,
    )
