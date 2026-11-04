from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

MODEL = "qwen2.5:3b"
KEEP_ALIVE = "2m"
NUM_CTX = 2048
HISTORY_LIMIT = 6

HISTORY_FILE = DATA_DIR / "history.json"
FACTS_FILE = DATA_DIR / "facts.txt"

ASSISTANT_NAME = "Sam"
FOLDERS_FILE = DATA_DIR / "folders.json"

ASSISTANT_NAME = "Sam"
FOLDERS_FILE = DATA_DIR / "folders.json"
