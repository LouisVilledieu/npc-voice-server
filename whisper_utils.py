import os
from typing import Optional

TRANSCRIBE_PROVIDER = "openai"
import openai


def transcribe(audio_path: str, language: Optional[str] = None) -> str:
    """Transcribe an audio file into text.

    Args:
        audio_path: Path to the audio file.
        language: ISO 639-1 language code. If None, Whisper auto-detects the language.

    Returns:
        Transcribed text.
    """
    from openai import OpenAI

    client = OpenAI()
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1", file=f, language=language
        )
    return response.text.strip()


def save_base64_to_tempfile(audio_base64: str, suffix: str = ".wav") -> str:
    """Save base64 audio data to a temporary file.

    Args:
        audio_base64: Base64 encoded string.
        suffix: Temporary file extension (".wav" or ".mp3").

    Returns:
        Path of the created file.
    """
    import base64, uuid, pathlib, re

    audio_base64 = re.sub(r"\s+", "", audio_base64 or "")

    padding_len = (-len(audio_base64)) % 4
    if padding_len:
        audio_base64 += "=" * padding_len

    try:
        audio_bytes = base64.b64decode(audio_base64, altchars=b"-_")
    except Exception as e:
        raise ValueError(f"Base64 decoding failed: {e}")

    tmp_dir = pathlib.Path(os.getenv("AUDIO_OUTPUT_DIR", "./audio_outputs"))
    tmp_dir.mkdir(parents=True, exist_ok=True)

    tmp_path = tmp_dir / f"tmp_{uuid.uuid4().hex}{suffix}"
    with open(tmp_path, "wb") as f:
        f.write(audio_bytes)

    return str(tmp_path)
