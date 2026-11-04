import re

from .tools.files import open_folder
from .tools.spotify import control

SPOTIFY = {
    "play": "play",
    "play music": "play",
    "resume": "play",
    "resume music": "play",
    "pause": "pause",
    "pause music": "pause",
    "stop music": "pause",
    "next": "next",
    "next song": "next",
    "skip": "next",
    "skip song": "next",
    "previous": "previous",
    "previous song": "previous",
    "go back": "previous",
    "volume up": "volume up",
    "louder": "volume up",
    "volume down": "volume down",
    "quieter": "volume down",
}

OPEN_PATTERN = re.compile(r"^open (?:my |the )?(.+?)(?: folder| directory)?$")


def route(text):
    """Return a reply if a keyword command matched, otherwise None."""
    t = text.lower().strip().rstrip(".!?")
    if t in SPOTIFY:
        return control(SPOTIFY[t])
    match = OPEN_PATTERN.match(t)
    if match:
        return open_folder(match.group(1))
    return None
