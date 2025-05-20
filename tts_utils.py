import os
import base64
import uuid
import pathlib
from typing import Optional

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TTS_PROVIDER = os.getenv("TTS_PROVIDER", "elevenlabs").lower()

if TTS_PROVIDER == "elevenlabs":
    from elevenlabs.client import ElevenLabs

    eleven_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY", "sk_ef982166cc836773c0861332a2ca795279bcbcb8d38e025d"))
else:
    raise ValueError("TTS_PROVIDER must be 'elevenlabs'")


def synthesize_speech(text: str, language: str = "fr", voice: Optional[str] = None) -> str:
    """Synthesize text into speech and return a base64-encoded string.

    Returns:
        base64 string of the generated audio file (MP3 format).
    """

    if TTS_PROVIDER == "elevenlabs":
        logger.info(f"Synthesizing speech for text: {text}")
        # Voice ID "Rachel" (public) available for all ElevenLabs keys.
        voice_id = voice or os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

        audio_chunks = eleven_client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format="mp3_44100_128"
        )
        # `convert` returns a generator of audio chunks (bytes). We join them to get the complete file.
        audio_bytes = b"".join(audio_chunks)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    else:
        raise RuntimeError("TTS provider not supported")

    return audio_b64
