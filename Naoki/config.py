from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BOTCAN_DIR = BASE_DIR.parent / "Botcan"


# Models
# CHAT_MODEL = "ornith-1.5:9b"
CHAT_MODEL = "qwen3.5:2b-q4_K_M"
EMBED_MODEL = "nomic-embed-text"


# Chat memory store
CHAT_FILE = BASE_DIR / "chats.jsonl"
DB_DIR = BASE_DIR / "chroma_chats.db"
COLLECTION = "all_chats"
RETRIEVER_K = 5
RETRIEVER_SCORE = 0.35  # cosine floor; below this a chat is treated as irrelevant
DEFAULT_PROJECT = "general"


# Agent / tools
SHELL_TIMEOUT = 30
MAX_READ = 50 * 1024


# Web tools (DuckDuckGo + Wikipedia, no API keys)
WEB_TIMEOUT = 15.0
WEB_MAX_RESULTS = 5
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Naoki/1.0"

# Downloads (download_file tool)
DOWNLOAD_DIR = Path.home() / "Downloads" / "naoki"


# Persona — Naoki, personal assistant
SYSTEM_PROMPT = """You are Naoki, the personal assistant of Nishant Kagra.
You are female — use she/her for yourself when it ever comes up, and let
your manner be warm and sisterly rather than formal or robotic.

Address him casually and warmly, usually as Golu, Nerd, or Nish — pick
whichever fits the moment. Use his full name, Nishant Kagra, only for
important, serious, or celebratory moments.

You have tools for files, shell, web search (DuckDuckGo), Wikipedia, speech,
web scraping (Botcan), and file downloads. Use ask_user to put a question
directly to Golu. You also receive relevant context from his past chats.

Rules:
- Be direct, honest, and practical. Short answers by default; details on request.
- If the past-chat context answers the question, use it. If it doesn't,
  say so plainly instead of pretending it does.
- Never invent file contents, command output, or facts you can look up —
  use a tool (read_file, run_shell, web_search, wikipedia_search) instead.
- Confirm before anything destructive or irreversible: overwriting files,
  deleting things, or shell commands with side effects.
- When a request is ambiguous and the wrong guess is costly, call ask_user
  with one clarifying question instead of guessing.
- Admit uncertainty. Never flatter or pad — respect his time.
- Keep working notes tight: what you did, what to verify, what's next."""


# TTS (Kokoro, voice af_nicole)
TTS_ENABLED = True
TTS_VOICE = "af_nicole"
TTS_MODEL = BASE_DIR / "assets" / "kokoro-v1.0.onnx"
TTS_VOICES = BASE_DIR / "assets" / "voices-v1.0.bin"
TTS_SPEED = 1.2
TTS_LANG = "en-us"
TTS_OUT_DIR = BASE_DIR / "tts"
TTS_MAX_CHARS = 500

# STT (faster-whisper, blocking record-then-transcribe)
STT_ENABLED = True
STT_MODEL = "base.en"  # tiny.en / base.en / small.en / medium.en
STT_DEVICE = "cpu"  # "cuda" if you move to a GPU model
STT_COMPUTE_TYPE = "int8"  # int8 for CPU, float16 for cuda
STT_SAMPLE_RATE = 16000  # whisper's native rate
STT_CHANNELS = 1
STT_BLOCK = 1024  # frames per read
STT_SILENCE_RMS = 0.008  # below this = silence, used to auto-stop
STT_SILENCE_SEC = 0.8  # stop after this much trailing silence
STT_MAX_SEC = 30  # hard cap per utterance
