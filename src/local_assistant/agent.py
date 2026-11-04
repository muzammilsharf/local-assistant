from .memory import add_fact, check_remember
from .router import route


def run_task(text):
    """Handle a Task request and return the reply text."""
    fact = check_remember(text)
    if fact:
        add_fact(fact)
        return f"Saved: {fact}"

    reply = route(text)
    if reply is not None:
        return reply
    return "I don't have a command for that yet. Model-powered tasks are coming next."
