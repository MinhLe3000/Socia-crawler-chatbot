"""
Central configuration for MongoDB and Qdrant connections.

All settings are read from environment variables (via .env file).
This is the SINGLE source of truth — scripts/ re-exports from here.
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from qdrant_client import QdrantClient

load_dotenv()

# --- MongoDB ---
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is not set. "
        "Create a .env file with MONGO_URI=mongodb+srv://... (see .env.example)"
    )

MONGO_DB_SOURCE = os.getenv("MONGO_DB_SOURCE", "Postandcmt")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "Chatbot")

# --- Qdrant ---
QDRANT_URL = os.getenv("QDRANT_URL")
if not QDRANT_URL:
    raise RuntimeError(
        "QDRANT_URL is not set. "
        "Create a .env file with QDRANT_URL=https://... (see .env.example)"
    )
QDRANT_KEY = os.getenv("QDRANT_KEY")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "knowledge_base")


def get_mongo_client() -> MongoClient:
    """Get MongoDB client instance."""
    return MongoClient(MONGO_URI)


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance."""
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_KEY,
    )

