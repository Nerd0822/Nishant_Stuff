import os
from pathlib import Path
from dotenv import load_dotenv

Base_dir = Path(__file__).resolve().parent
root = Path(__file__).resolve().parent.parent
load_dotenv(Base_dir / ".env")

MODEL = os.environ.get("model")
EMBED_MODEL = os.environ.get("embed_model")

# Persona lives in its own file, not .env: it is multi-line and full of quotes,
# which .env cannot represent (an embedded " ends the value and orphans the rest).
PERSONA = (Base_dir / "persona.txt").read_text(encoding="utf-8") if (Base_dir / "persona.txt").exists() else None

# Where file tools stash the original before write/create/delete
BACKUP_DIR = Base_dir / "data" / "backups"

# Append-only transcript of every conversation
CHAT_LOG = Base_dir / "data" / "chats.jsonl"

# database dir
DB_DIR = Base_dir / "data" / "chroma_db"

# Shell tool ceiling: an interactive command hangs until this kills it
SHELL_TIMEOUT = 30

# Web tools
WEB_TIMEOUT = 15.0
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) Naoki/1.0"

# Where download_file saves
DOWNLOADS_DIR = Path.home() / "Downloads"
