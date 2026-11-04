from datetime import datetime

import ollama

from .config import ASSISTANT_NAME, KEEP_ALIVE, MODEL, NUM_CTX
from .memory import load_facts


def build_system_prompt():
    today = datetime.now().strftime("%A, %Y-%m-%d")
    prompt = (
        f"You are {ASSISTANT_NAME}, a helpful local desktop assistant. "
        f"Today is {today}."
    )
    facts = load_facts()
    if facts:
        prompt += f"\nKnown facts about the user:\n{facts}"
    return prompt


def build_messages(history, user_text):
    return (
        [{"role": "system", "content": build_system_prompt()}]
        + history
        + [{"role": "user", "content": user_text}]
    )


def stream_chat(history, user_text):
    """Yield the reply piece by piece as the model generates it."""
    stream = ollama.chat(
        model=MODEL,
        messages=build_messages(history, user_text),
        keep_alive=KEEP_ALIVE,
        options={"num_ctx": NUM_CTX},
        stream=True,
    )
    for chunk in stream:
        yield chunk["message"]["content"]
