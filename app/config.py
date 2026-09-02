import os
import sys
from pathlib import Path

# Base data and working directory
BASE_DIR = Path.cwd()

DATA_DIR = Path(os.getenv("UNIPLAG_DATA", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "uniplag.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("UNIPLAG_DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")
SECRET_KEY = os.getenv("UNIPLAG_SECRET", "change-me-in-production-please")

SHINGLE_K = 5
MINHASH_PERM = 256
LSH_BANDS = 64
LSH_ROWS = MINHASH_PERM // LSH_BANDS
CANDIDATE_THRESHOLD = 0.02
MAX_SOURCES = 10
MIN_FRAG_WORDS = SHINGLE_K
EXACT_SCAN_LIMIT = 20000

AI_MODEL_DIR = Path(os.getenv("UNIPLAG_AI_MODEL", BASE_DIR / "models" / "ai-detector"))
AI_THRESHOLD_WARN = 0.6
OLLAMA_URL = os.getenv("UNIPLAG_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("UNIPLAG_OLLAMA_MODEL", "")
OLLAMA_CHUNK_CHARS = 1500

MAX_UPLOAD_BYTES = 20 * 1024 * 1024

# Aris Directive v0.4.1 TASK_1: порог, с которого ICG fast-контур обрабатывается
# в отдельном пуле (_icg_executor), не занимая воркеры пула проверок.
ICG_LARGE_WORDS = 5000
