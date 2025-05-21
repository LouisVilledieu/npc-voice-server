import base64
import os
import mimetypes
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from whisper_utils import save_base64_to_tempfile, transcribe
from llm_utils import generate_npc_response
from tts_utils import synthesize_speech
from db_utils import close_connection, get_db
from users_routes import router as users_router
from npc_routes import router as npcs_router, Npc
from users_routes import User

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vocal RPG NPC Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(npcs_router)

class NpcInteractionRequest(BaseModel):
    npc_id: str = Field(..., description="NPC identifier")
    player_id: str = Field(..., description="Player identifier")
    audio_base64: Optional[str] = Field(
        None,
        description="Audio encoded in base64 (.wav or .mp3) - required if mode='audio'",
    )
    text: Optional[str] = Field(
        None,
        description="Text input by the player - required if mode='text'",
    )
    language: str = Field("fr", description="ISO 639-1 language code (fr, en, ...)")
    mode: str = Field("audio", description="Interaction mode (audio or text)")


class NpcInteractionResponse(BaseModel):
    transcript: str
    llm_response: str
    audio_response_base64: str


@app.post("/npc_interaction", response_model=NpcInteractionResponse)
async def npc_interaction(payload: NpcInteractionRequest):
    """Main route receiving player's audio and returning NPC's vocal response."""

    if payload.mode == "audio":
        if not payload.audio_base64:
            raise HTTPException(status_code=400, detail="audio_base64 is required in audio mode")

        logger.info(f"Received audio base64: {payload.audio_base64[:10]}...")

        suffix = ".wav"
        if payload.audio_base64.startswith("data:"):
            try:
                mime_type = payload.audio_base64.split(";")[0].split(":")[1]
                suffix = mimetypes.guess_extension(mime_type) or ".wav"
                audio_b64_clean = payload.audio_base64.split(",", 1)[1]
            except Exception:
                audio_b64_clean = payload.audio_base64
        else:
            audio_b64_clean = payload.audio_base64

        audio_path = save_base64_to_tempfile(audio_b64_clean, suffix=suffix)

        try:
            transcript = transcribe(audio_path, language=payload.language)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Whisper error: {e}")

    elif payload.mode == "text":
        logger.info(f"Received text with length: {len(payload.text) if payload.text else 0}")
        if not payload.text:
            raise HTTPException(status_code=400, detail="text is required in text mode")
        transcript = payload.text

    else:
        raise HTTPException(status_code=400, detail="Unsupported mode (audio or text)")

    try:
        logger.info(f"Transcript: {transcript}")
        llm_response = generate_npc_response(
            npc_id=payload.npc_id,
            player_id=payload.player_id,
            transcript=transcript,
            language=payload.language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")
    logger.info(f"LLM response: {llm_response}")

    logger.info(f"Synthesizing speech for text: {llm_response}")
    try:
        audio_response_b64 = synthesize_speech(
            text=llm_response, language=payload.language, npc_id=payload.npc_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")
    logger.info(f"Audio response base64: {audio_response_b64[:10]}...")

    return NpcInteractionResponse(
        transcript=transcript,
        llm_response=llm_response,
        audio_response_base64=audio_response_b64,
    )


@app.get("/npc_list")
async def npc_list():
    """Returns the list of NPCs."""
    db = get_db()
    npcs = db["npcs"].find()
    return [Npc(**npc) for npc in npcs]


@app.get("/user_list")
async def user_list():
    """Returns the list of users."""
    db = get_db()
    users = db["users"].find()
    return [User(**user) for user in users]


@app.on_event("shutdown")
async def shutdown_event():
    close_connection()
