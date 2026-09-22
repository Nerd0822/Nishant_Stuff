from pathlib import Path

# Models
PRIMARY_MODEL = "qwen3.5:2b-q4_K_M"
ADVANCED_MODEL = "ornith-1.5:9b"
PRIMARY_KEEP_ALIVE = 600  # seconds the primary model stays loaded between turns
ADVANCED_KEEP_ALIVE = 0  # seconds the advanced model stays loaded (0 = unload right after answering)

# Memory: keep only one model resident at a time. A 2B and a 9B loaded
# together can exhaust VRAM, so the other model is evicted before a load.
SWAP_MODELS = True
MODEL_CMD_TIMEOUT = 5  # seconds ps/unload requests may take (never hang the CLI)

# Agent limits
MAX_TURNS = 10
MAX_TOOL_CHARS = 20000
COMMAND_TIMEOUT = 60

# Context window: only the last N messages are sent to the model each turn.
# The full conversation is persisted to history.json regardless.
MAX_MESSAGES = 5
MAX_PREDICT_TOKENS = 1024
MAX_NUM_CTX = None

# Data files (stored next to the package)
BASE_DIR = Path(__file__).resolve().parent
HISTORY_FILE = BASE_DIR / "history.json"
ABOUT_ME_FILE = BASE_DIR / "about_me.json"

# Web search — fill both to use Google Custom Search; empty falls back to DuckDuckGo
GOOGLE_API_KEY = ""
GOOGLE_CSE_ID = ""

# TTS: Kokoro v1.0 through kokoro-onnx (offline, CPU, one engine only)
TTS_ENABLED = True
TTS_VOICE = "af_nicole"       # any of the 54 names in voices-v1.0.bin
TTS_SPEED = 1.0
TTS_REALTIME = True           # speak chunks while the rest is still rendering
TTS_MODEL = BASE_DIR / "models" / "kokoro-v1.0.onnx"
TTS_VOICES = BASE_DIR / "models" / "voices-v1.0.bin"
TTS_MAX_CHARS = 600

# TUI
TUI_TOOL_PREVIEW_CHARS = 1200