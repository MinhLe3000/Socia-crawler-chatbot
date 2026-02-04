"""Configuration settings for MongoDB connection."""

from pymongo import MongoClient

# MongoDB Connection URI
MONGO_URI = "mongodb+srv://mle333999_db:LGWX15KzZEZSXxRS@deandatabase.uuskv7o.mongodb.net/?appName=Deandatabase"

# Database names
# Database chứa posts và comments (đọc dữ liệu nguồn)
MONGO_DB_SOURCE = "Postandcmt"  # Database chứa posts và comments

# Database chứa knowledge_base và chatlogs (ghi dữ liệu RAG)
MONGO_DB_NAME = "Chatbot"  # Database chứa knowledge_base (cho RAG)


def get_mongo_client() -> MongoClient:
    """Get MongoDB client instance."""
    return MongoClient(MONGO_URI)

