import inspect
import re

from .llm import ask_with_tools
from .memory import add_fact, check_remember
from .router import route
from .tools import TOOLS
from .tools.documents import create_document

CREATION_VERBS = re.compile(
    r"\b(create|make|write|generate|draft|prepare)(?:s|d|ed|ing)?\b",
    re.IGNORECASE,
)
DOCUMENT_WORDS = re.compile(
    r"\b(document|doc|report|summary|odt|essay)s?\b|\b(notes|summaries)\b",
    re.IGNORECASE,
)


def detect_document_request(text: str):
    """Detect if the user is asking to create a document without calling a model.

    Returns (title, instructions) if matched, otherwise None.
    """
    if not text:
        return None
    if not (CREATION_VERBS.search(text) and DOCUMENT_WORDS.search(text)):
        return None

    instructions = text.strip()

    # 1. Text after "called", "titled", "named" (strip quotes)
    named_match = re.search(
        r"\b(?:called|titled|named)\s+([^\n\r]+)", text, re.IGNORECASE
    )
    if named_match:
        raw_title = named_match.group(1).strip()
        quote_match = re.search(r"^[\"']([^\"']+)[\"']", raw_title)
        if quote_match:
            title = quote_match.group(1).strip()
        else:
            unquoted = re.split(r"\s+\bwith\b\s+", raw_title, maxsplit=1, flags=re.IGNORECASE)[0]
            title = unquoted.strip("\"'").rstrip(".!?").strip()
        if title:
            return (title, instructions)

    # 2. Words after "about" or "on" (max 6 words, title-cased)
    about_match = re.search(
        r"\b(?:about|on)\s+([^\n\r]+)", text, re.IGNORECASE
    )
    if about_match:
        raw_about = about_match.group(1).strip().strip("\"'").rstrip(".!?")
        words = raw_about.split()[:6]
        if words:
            title = " ".join(words).title()
            return (title, instructions)

    # 3. Fallback
    return ("Document", instructions)


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

    # 2. Fast path for document requests, no model tool-picking needed
    doc_req = detect_document_request(text)
    if doc_req is not None:
        title, instructions = doc_req
        return create_document(title, instructions)

    # 3. Let the model pick a tool
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
