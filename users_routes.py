from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from db_utils import get_db

router = APIRouter()


class CreateUserRequest(BaseModel):
    user_id: str = Field(..., description="User identifier / name")

class User(BaseModel):
    user_id: str = Field(alias="_id")
    history: dict

    model_config = ConfigDict(populate_by_name=True)

@router.post("/user", status_code=201, summary="Create a new user")
def create_user(payload: CreateUserRequest):
    """add new user to the database"""
    db = get_db()
    if db["users"].find_one({"_id": payload.user_id}):
        raise HTTPException(status_code=409, detail="Already exists")
    db["users"].insert_one({"_id": payload.user_id, "history": {}})
    return {"message": "User created", "user_id": payload.user_id}


@router.get("/users/{user_id}", summary="Get user history")
def get_user_history(user_id: str):
    """get user history from the database"""
    db = get_db()
    user = db["users"].find_one({"_id": user_id})
    return user["history"]

