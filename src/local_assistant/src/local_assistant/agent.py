from .router import route


def run_task(text):
    """Handle a Task mode request and return the reply text."""
    reply = route(text)
    if reply is not None:
        return reply
    return "I don't have a command for that yet. Model-powered tasks are coming next."
