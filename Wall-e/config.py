from pathlib import Path

# Models
# PRIMARY_MODEL = "llama3.2:1b"
# PRIMARY_MODEL = "qwen3:0.6b"
# PRIMARY_MODEL = "qwen3:1.7b"
PRIMARY_MODEL = "ornith-1.5:9b"
ADVANCED_MODEL = "ornith-1.5:9b"  # exact local tag
ADVANCED_KEEP_ALIVE = 0  # seconds the advanced model stays loaded (0 = unload right after answering)

# Agent limits
MAX_TURNS = 5            # model <-> tool round trips allowed per request
MAX_TOOL_CHARS = 20000   # tool output is truncated to this many characters
COMMAND_TIMEOUT = 60     # seconds before run_shell is killed

# Context management — controls how much conversation history is sent to the
# model on every call. The *full* conversation is still saved to
# history.json for persistence; only the last MAX_MESSAGES messages are sent
# to the model so that responses stay fast even in long-running sessions.
# Set to None (or a very large number) to send the entire conversation.
MAX_MESSAGES = 5        # last N messages kept for the model context window
MAX_PREDICT_TOKENS = 1024  # caps tokens the model generates in a single reply
MAX_NUM_CTX = None      # set e.g. 4096 to cap the model's context window; None = model default

# Files (kept next to the code, not in the current directory)
BASE_DIR = Path(__file__).resolve().parent
HISTORY_FILE = BASE_DIR / "history.json"    # conversation log, saved every turn
ABOUT_ME_FILE = BASE_DIR / "about_me.json"  # user facts, written by remember_fact

# Web search (optional): fill both to use the official Google Custom Search
# API in search_web. Empty values fall back to DuckDuckGo (no key needed).
GOOGLE_API_KEY = ""
GOOGLE_CSE_ID = ""

# Text to speech: "flite" (installed, offline) | "edge" (pip install edge-tts,
# online) | "kokoro" (pip install kokoro-onnx soundfile + models in ./models).
# speak() falls back to flite whenever the chosen engine is unavailable.
TTS_ENABLED = True
TTS_ENGINE = "edge"
TTS_VOICE = "slt"  # flite voice (female)
TTS_EDGE_VOICE = "en-US-AriaNeural"  # edge-tts voice (female)
TTS_KOKORO_VOICE = "af_heart"  # kokoro voice (female)
TTS_KOKORO_MODEL = BASE_DIR / "models" / "kokoro-v1.0.onnx"
TTS_KOKORO_VOICES = BASE_DIR / "models" / "voices-v1.0.bin"
TTS_MAX_CHARS = 600  # replies are cut to this before speaking
TUI_TOOL_PREVIEW_CHARS = 1200  # tool-call preview length shown in the TUI
