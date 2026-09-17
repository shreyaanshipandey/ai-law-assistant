"""
Alternative MongoDB (Motor) connection setup, provided as a drop-in
replacement for db/database.py if you prefer NoSQL over PostgreSQL.
Not wired into main.py by default — see README for how to switch.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        # e.g. MONGO_URL=mongodb://localhost:27017
        _client = AsyncIOMotorClient(settings.DATABASE_URL)
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    return get_mongo_client()["ai_law_assistant"]


# Collections (created lazily by Mongo on first write):
#   users, cases, petitions, chat_sessions, bns_sections
