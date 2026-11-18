import inspect

from .llm import ask_with_tools
from .memory import add_fact, check_remember
from .router import route
from .tools import TOOLS


def _sanitize_args(tool, raw_args):
    """Align model-provided arguments with the tool function signature."""
    sig = inspect.signature(tool)
    known = {}
    unknown = {}
    for k, v in (raw_args or {}).items():
        if k in sig.parameters:
            known[k] = v
        else:
            unknown[k] = v

    missing = [
        name
        for name, param in sig.parameters.items()
        if param.default is inspect.Parameter.empty
        and param.kind
        not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        and name not in known
    ]

    if len(missing) == 1 and len(unknown) == 1:
        val = next(iter(unknown.values()))
        if isinstance(val, str):
            known[missing[0]] = val

    return known


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
            args = _sanitize_args(tool, call.function.arguments)
            results.append(tool(**args))
        except Exception as e:
            results.append(f"That didn't work: {e}")
    return "\n".join(results)
