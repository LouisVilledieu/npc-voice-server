from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

from db_utils import get_db

router = APIRouter()

class Npc(BaseModel):
    npc_id: str = Field(alias="_id")
    description: str
    voice_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

@router.post("/npc", status_code=201, summary="Create a new NPC")
def create_npc(payload: Npc):
    """create a new NPC"""
    db = get_db()
    if db["npcs"].find_one({"_id": payload.npc_id}):
        raise HTTPException(status_code=409, detail="NPC already exists")
    db["npcs"].insert_one({"_id": payload.npc_id, "description": payload.description, "voice_id": payload.voice_id})
    return {"message": "NPC created", "npc_id": payload.npc_id}

@router.get("/npc/{npc_id}", summary="Get NPC")
def get_npc_description(npc_id: str):
    """get NPC from the database"""
    db = get_db()
    npc = db["npcs"].find_one({"_id": npc_id})
    return npc

@router.put("/npc/{npc_id}/description", summary="Update NPC description")
def update_npc_description(npc_id: str, description: str):
    """update NPC description"""
    db = get_db()
    db["npcs"].update_one({"_id": npc_id}, {"$set": {"description": description}})
    return {"message": "NPC description updated"}

@router.put("/npc/{npc_id}/voice_id", summary="Update NPC voice_id")
def update_npc_voice_id(npc_id: str, voice_id: str):
    """update NPC voice_id"""
    db = get_db()
    db["npcs"].update_one({"_id": npc_id}, {"$set": {"voice_id": voice_id}})