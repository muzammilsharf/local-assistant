import sys
from datetime import datetime

import ollama

from .config import (
    ASSISTANT_NAME,
    KEEP_ALIVE,
    MAX_TASK_TOKENS,
    MAX_WRITE_TOKENS,
    MODEL,
    NUM_CTX,
    TASK_MODEL,
    WRITER_MODEL,
)
from .memory import load_facts

TASK_PROMPT = (
    f"You are {ASSISTANT_NAME}, a desktop assistant. When the user asks for an "
    "action, call the matching tool. If no tool fits, answer in one short sentence."
)

WRITER_PROMPT = (
    "You write short documents. Reply with the document text only, with no intro "
    "and no closing remarks. Use this format: a line '# Summary', then one short "
    "paragraph, then a line '# Key points', then bullet lines that each start "
    "with '- ' and state a real, specific point. Follow any structure or number "
    "of points the user asks for. Keep it under 200 words.\n\n"
    "Example for a document about the water cycle:\n"
    "# Summary\n"
    "Water moves between the oceans, the air and the land in a continuous loop.\n"
    "# Key points\n"
    "- Heat from the sun evaporates water from oceans and lakes.\n"
    "- Water vapor cools and condenses into clouds.\n"
    "- Rain and snow return water to the ground and rivers."
)


def _secs(ns):
    return round((ns or 0) / 1e9, 1)


def log_timing(label, r):
    print(
        f"[{label}] load {_secs(r.load_duration)}s | "
        f"prompt {r.prompt_eval_count} tok in {_secs(r.prompt_eval_duration)}s | "
        f"wrote {r.eval_count} tok in {_secs(r.eval_duration)}s | "
        f"total {_secs(r.total_duration)}s",
        file=sys.stderr,
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
    log_timing("task", response)
    return response.message


def write_document_text(title, instructions):
    """Write the body of a document as plain text."""
    response = ollama.chat(
        model=WRITER_MODEL,
        messages=[
            {"role": "system", "content": WRITER_PROMPT},
            {"role": "user", "content": f"Title: {title}\nWhat to write: {instructions}"},
        ],
        keep_alive=KEEP_ALIVE,
        options={
            "num_ctx": NUM_CTX,
            "num_predict": MAX_WRITE_TOKENS,
            "temperature": 0.4,
        },
    )
    log_timing("write", response)
    return response.message.content.strip()
