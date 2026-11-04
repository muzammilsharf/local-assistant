import json

from .config import FACTS_FILE, HISTORY_FILE, HISTORY_LIMIT


def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text())[-HISTORY_LIMIT:]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(messages):
    HISTORY_FILE.write_text(json.dumps(messages[-HISTORY_LIMIT:], indent=2))


def load_facts():
    try:
        return FACTS_FILE.read_text().strip()
    except FileNotFoundError:
        return ""


def add_fact(text):
    with FACTS_FILE.open("a") as f:
        f.write(text.strip() + "\n")


def check_remember(text):
    """Return the fact if the text starts with a remember trigger, else None."""
    lower = text.lower().strip()
    for trigger in ("remember this", "remember that", "remember:"):
        if lower.startswith(trigger):
            return text.strip()[len(trigger):].strip(" :,")
    return None
