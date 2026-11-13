from .llm import ask_with_tools
from .memory import add_fact, check_remember
from .router import route
from .tools import TOOLS


def run_task(text):
    """Handle a Task request and return the reply text."""
    fact = check_remember(text)
    if fact:
        add_fact(fact)
        return f"Saved: {fact}"

    # 1. Instant keyword commands, no model needed
    reply = route(text)
    if reply is not None:
        return reply

    # 2. Let the model pick a tool
    message = ask_with_tools(text, list(TOOLS.values()))
    if not message.tool_calls:
        return message.content or "I'm not sure what to do with that."

    results = []
    for call in message.tool_calls:
        tool = TOOLS.get(call.function.name)
        if tool is None:
            results.append(f"I don't have a tool called {call.function.name}.")
            continue
        try:
            results.append(tool(**call.function.arguments))
        except Exception as e:
            results.append(f"That didn't work: {e}")
    return "\n".join(results)
