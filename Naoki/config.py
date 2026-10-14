import os
from pathlib import Path
from dotenv import load_dotenv

Base_dir = Path(__file__).resolve().parent
root = Path(__file__).resolve().parent.parent
load_dotenv(Base_dir / ".env")


ART = """
███▄██ ██▀██ ██▀██ ██ ██ ▀██▀
██ ▀██ ██▄██ ██ ██ ██▄█▀  ██ 
█▓░ █▓ █▓░█▓ █▓░█▓ █▓░█▓  █▓░
▀▀  ▀▀ ▀▀ ▀▀ ▀▀▀▀▀ ▀▀ ▀▀ ▀▀▀▀
"""

MODEL = os.environ.get("model")  # model for chat
EMBED_MODEL = os.environ.get("embed_model")  # model for embedding

SYSTEM = """
your name is naoki and you are a personal assistant, keep the reply short and to the point.
"""

# --- values the tools/ package imports ---
BACKUP_DIR = Base_dir / "data" / "backups"
DOWNLOADS_DIR = Path.home() / "Downloads"
MEMORY_DIR = Base_dir / "data" / "memory.jsonl"

# Shell tool ceiling: an interactive command hangs until this kills it
SHELL_TIMEOUT = 30

# Web tools
WEB_TIMEOUT = 15.0
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) Naoki/1.0"

# --- rag ---
DB_DIR = Base_dir / "data" / "chroma_db"
