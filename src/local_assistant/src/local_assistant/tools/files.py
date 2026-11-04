import json
import subprocess
from pathlib import Path

from ..config import FOLDERS_FILE


def load_folders():
    try:
        raw = json.loads(FOLDERS_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {name.lower(): Path(path).expanduser() for name, path in raw.items()}


def open_folder(name):
    folders = load_folders()
    path = folders.get(name.lower().strip())
    if path is None:
        known = ", ".join(sorted(folders)) or "none yet"
        return f"I don't know a folder called '{name}'. Known folders: {known}."
    if not path.is_dir():
        return f"{path} doesn't exist."
    subprocess.Popen(
        ["xdg-open", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return f"Opened {name}."
