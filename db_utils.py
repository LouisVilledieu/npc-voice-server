from typing import Dict, List

import os
from pymongo import MongoClient

MONGO_URI: str = os.getenv(
    "MONGO_URI")
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME")

_client: MongoClient | None = None
_db = None


def get_db():
    """Returns (and initializes if needed) the MongoDB database instance."""
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI)
        _db = _client[MONGO_DB_NAME]
        _ensure_seed_data(_db)
    return _db


def _ensure_seed_data(db):
    """Inserts test NPC and user if collections are empty."""
    if db["npcs"].count_documents({}) == 0:
        db["npcs"].insert_one(
            {
                "_id": "npc_test",
                "description": "A woman who runs a clothing store. She is very attentive and curious about the people around her.",
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
            }
        )

    if db["users"].count_documents({}) == 0:
        db["users"].insert_one(
            {
                "_id": "user_test",
                "history": {"npc_test": []},
            }
        )


def close_connection():
    """Closes the Mongo client"""
    global _client
    if _client is not None:
        _client.close() 