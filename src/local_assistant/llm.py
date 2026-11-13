from datetime import datetime

import ollama

from .config import (
    ASSISTANT_NAME,
    KEEP_ALIVE,
    MAX_TASK_TOKENS,
    MODEL,
    NUM_CTX,
    TASK_MODEL,
)
from .memory import load_facts

TASK_PROMPT = (
    f"You are {ASSISTANT_NAME}, a desktop assistant. When the user asks for an "
    "action, call the matching tool. When creating a document, write the full "
    "text in the content argument, keep it under 250 words, and use '# ' for "
    "headings. If no tool fits, answer in one short sentence."
)


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
    """Chat mode: yield the reply piece by piece as the model generates it."""
    stream = ollama.chat(
        model=MODEL,
        messages=build_messages(history, user_text),
        keep_alive=KEEP_ALIVE,
        options={"num_ctx": NUM_CTX},
        stream=True,
    )
    for chunk in stream:
        yield chunk["message"]["content"]


def ask_with_tools(user_text, tools):
    """Task mode: let the small model pick a tool. Returns the model message."""
    response = ollama.chat(
        model=TASK_MODEL,
        messages=[
            {"role": "system", "content": TASK_PROMPT},
            {"role": "user", "content": user_text},
        ],
        tools=tools,
        keep_alive=KEEP_ALIVE,
        options={
            "num_ctx": NUM_CTX,
            "num_predict": MAX_TASK_TOKENS,
            "temperature": 0.2,
        },
    )
    return response.message
