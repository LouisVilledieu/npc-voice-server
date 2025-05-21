import os
import logging
from typing import Dict

from db_utils import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()


def _get_npc_description(db, npc_id: str) -> str:
    npc = db["npcs"].find_one({"_id": npc_id})
    if npc and "description" in npc:
        return npc["description"]
    return "Undefined character."


def _get_history(db, player_id: str, npc_id: str, limit: int = 10) -> str:
    user = db["users"].find_one({"_id": player_id})
    history_str = ""
    if user and "history" in user and npc_id in user["history"]:
        history_list = user["history"][npc_id][-limit:]
        for exchange in history_list:
            history_str += f"Player: {exchange.get('player', '')} | NPC: {exchange.get('npc', '')}. "
    return history_str.strip()


def _store_history(db, player_id: str, npc_id: str, player_msg: str, npc_msg: str):
    history_entry = {"player": player_msg, "npc": npc_msg}

    user = db["users"].find_one({"_id": player_id}, {"history": 1})
    if not user:
        db["users"].insert_one({
            "_id": player_id,
            "history": {npc_id: [history_entry]},
        })
        return

    if "history" not in user or not isinstance(user["history"], dict):
        db["users"].update_one({"_id": player_id}, {"$set": {"history": {}}})

    if db["users"].count_documents({"_id": player_id, f"history.{npc_id}": {"$exists": False}}):
        db["users"].update_one({"_id": player_id}, {"$set": {f"history.{npc_id}": []}})

    db["users"].update_one(
        {"_id": player_id},
        {"$push": {f"history.{npc_id}": history_entry}},
    )


def build_npc_prompt(npc_id: str, player_id: str, transcript: str, language: str) -> str:
    db = get_db()
    npc_description = _get_npc_description(db, npc_id)
    npc_history = _get_history(db, player_id, npc_id)

    prompt_parts = [
        f"Context: Player '{player_id}' is interacting with non-player character '{npc_id}'.",
        f"Language of the conversation: {language}.",
        f"NPC Description: {npc_description}.",
    ]

    if npc_history:
        prompt_parts.append(f"Recent conversation history between the player and the NPC: {npc_history}")

    prompt_parts.append(f"Current player message: \"{transcript}\".")
    prompt_parts.append(
        "Respond strictly in character (roleplay), taking into account the history and the NPC's personality. "
        "The response should feel natural and human, and be adapted to the player's message. "
        "React as if you already know the player, if a prior relationship exists. "
        "Be consistent, concise, and respond in the specified language. "
        "Keep replies short and natural-sounding."
    )

    return " ".join(prompt_parts)


def generate_npc_response(npc_id: str, player_id: str, transcript: str, language: str = "en") -> str:
    """Generates the NPC's response and saves the exchange to history."""

    prompt = build_npc_prompt(npc_id, player_id, transcript, language)
    logger.info(f"Prompt: {prompt}")

    response_text: str

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
        response_text = response.choices[0].message.content.strip()
        logger.info(f"Response: {response_text}")

    elif LLM_PROVIDER == "groq":
        from groq import Groq

        model_name = os.getenv("LLM_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        logger.info(f"LLM_MODEL: {model_name}")

        client = Groq()
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an NPC in a video game."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        response_text = response.choices[0].message.content.strip()
        logger.info(f"Response: {response_text}")

    else:
        raise RuntimeError("Unsupported LLM provider.")

    try:
        _store_history(get_db(), player_id, npc_id, transcript, response_text)
    except Exception as e:
        logger.warning(f"Failed to store conversation history: {e}")

    return response_text
