import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("SAM_DATA_DIR", ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "qwen2.5:3b"
KEEP_ALIVE = "2m"
NUM_CTX = 2048
HISTORY_LIMIT = 6

HISTORY_FILE = DATA_DIR / "history.json"
FACTS_FILE = DATA_DIR / "facts.txt"

ASSISTANT_NAME = "Sam"
FOLDERS_FILE = DATA_DIR / "folders.json"
TASK_CLOSE_SECONDS = 3
TASK_MODEL = "qwen2.5:1.5b"
OUTPUT_DIR = Path(os.environ.get("SAM_OUTPUT_DIR", Path.home() / "Documents" / "Sam"))
MAX_TASK_TOKENS = 600
WRITER_MODEL = TASK_MODEL
MAX_WRITE_TOKENS = 450
