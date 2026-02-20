"""
Thin re-export so scripts can still do ``from config import ...``.

All actual values live in src/utils/config.py (the single source of truth).
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.utils.config import (  # noqa: E402, F401
    MONGO_URI,
    MONGO_DB_SOURCE,
    MONGO_DB_NAME,
    QDRANT_URL,
    QDRANT_KEY,
    QDRANT_COLLECTION_NAME,
    get_mongo_client,
    get_qdrant_client,
)
