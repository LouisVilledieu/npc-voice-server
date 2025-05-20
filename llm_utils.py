import os
from typing import Dict

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

def build_npc_prompt(npc_id: str, player_id: str, transcript: str, language: str) -> str:
    """Build a basic prompt for the NPC.
    A history in the database and a description of every NPC will be available in the future in a database.
    """
    npc_description = "Is a young woman who runs a clothing store. She is very caring and curious about life and the people around her."
    npc_history = ""
    return (
        f"Player {player_id} is talking to NPC {npc_id}. "
        f"Language: {language}. "
        f"Player's message: '{transcript}'. "
        f"NPC description: {npc_description}. "
        f"History of your conversations: {npc_history}. "
        "Respond as the NPC, concisely and roleplay in the specified language (French or English)."
    )


def generate_npc_response(npc_id: str, player_id: str, transcript: str, language: str = "fr") -> str:
    """Generate an NPC response via the LLM."""

    prompt = build_npc_prompt(npc_id, player_id, transcript, language)
    logger.info(f"Prompt: {prompt}")

    if LLM_PROVIDER == "openai":
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a non-player character (NPC) in a video game."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        logger.info(f"Response: {response.choices[0].message.content.strip()}")
        return response.choices[0].message.content.strip()

    if LLM_PROVIDER == "groq":
        logger.info(f"LLM_MODEL: {os.getenv('LLM_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct')}")
        from groq import Groq
        client = Groq()
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"),
            messages=[
                {"role": "system", "content": "You are an NPC in a video game."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        logger.info(f"Response: {response.choices[0].message.content.strip()}")
        return response.choices[0].message.content.strip()

    raise RuntimeError("LLM provider not supported")
