import os
import base64
import uuid
import pathlib
from typing import Optional

from db_utils import get_db

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TTS_PROVIDER = os.getenv("TTS_PROVIDER", "elevenlabs").lower()

if TTS_PROVIDER == "elevenlabs":
    from elevenlabs.client import ElevenLabs

    eleven_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
else:
    raise ValueError("TTS_PROVIDER must be 'elevenlabs'")


def get_voice_id(npc_id: str) -> str:
    db = get_db()
    npc = db["npcs"].find_one({"_id": npc_id})
    if npc and "voice_id" in npc:
        return npc["voice_id"]
    return os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")


def synthesize_speech(text: str, language: str = "fr", npc_id: str = "npc_test") -> str:
    """Synthesize text into speech and return a base64-encoded string.

    Returns:
        base64 string of the generated audio file (MP3 format).
    """

    if TTS_PROVIDER == "elevenlabs":
        logger.info(f"Synthesizing speech for text: {text}")
        voice_id = get_voice_id(npc_id)
        model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

        audio_chunks = eleven_client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format="mp3_44100_128"
        )
        audio_bytes = b"".join(audio_chunks)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    else:
        raise RuntimeError("TTS provider not supported")

    return audio_b64
