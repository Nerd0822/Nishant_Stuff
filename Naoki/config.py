"""Settings. Two brains: a small chat model for talk, ornith for tool work."""

# ornith-1.5:9b is the whole stack: it calls tools, reasons, writes code,
# and sees screenshots (it ships a CLIP projector). No second model, no
# API keys, nothing remote.
PRIMARY_MODEL = "ornith-1.5:9b"

# Tool output is pasted into the prompt, so cap it. 20000 chars is enough
# for a file view without drowning a 9B model running locally.
MAX_TOOL_CHARS = 20000

# Shell commands are killed after this. 60s covers git/builds; anything
# longer should be a background job, not a blocked assistant turn.
COMMAND_TIMEOUT = 60

from pathlib import Path as _Path

# Everything the web tools save lands here by default. A subfolder of the
# real ~/Downloads keeps Naoki's fetches separate from the user's own.
DOWNLOAD_DIR = _Path.home() / "Downloads" / "naoki"

# Largest single download_file. 1 GB covers ISOs and datasets while still
# bounding disk abuse; anything bigger should be a manual curl/wget.
DOWNLOAD_MAX_BYTES = 1024 * 1024 * 1024

# Per-download network timeout. 120s covers slow servers; yt-dlp media
# downloads get their own longer budget inside tools/downloads.py.
DOWNLOAD_TIMEOUT = 120

# Two brains: CHAT_MODEL handles pure conversation (fast, no tools),
# PRIMARY_MODEL does everything that touches the machine (tools bound).
# A "!" prefix forces the big model for one turn; memory questions and
# anything with links/paths/action verbs always go big automatically.
CHAT_MODEL = "qwen3.5:2b-q4_K_M"

# Speech to text (/talk command): arecord captures, faster-whisper
# transcribes offline. "small" is the Hindi-capable pick; "tiny"/"base"
# are faster but mangle Devanagari speech.
STT_MODEL = "small"
STT_SECONDS = 10  # default recording length for /talk
STT_MAX_SECONDS = 30

# Project dir (voice models, index, and memory files live next to the code).
BASE_DIR = _Path(__file__).resolve().parent

# Text to speech: "flite" (installed, offline) | "edge" (edge-tts in the
# venv bin, needs internet) | "kokoro" (pip install kokoro-onnx soundfile
# + model files in ./models). speak() falls back to flite whenever the
# chosen engine is unavailable, so speech degrades instead of dying.
TTS_ENABLED = True
TTS_ENGINE = "kokoro"  # her voice, offline. Nothing else is wired.
TTS_VOICE = "slt"  # flite voice (female)
TTS_EDGE_VOICE = "en-US-AriaNeural"  # edge-tts voice (female)
# Attitude dials: faster + slightly higher pitch reads confident and
# commanding rather than soft. Neutral default -- tune only by ear.
TTS_EDGE_RATE = "+0%"
TTS_EDGE_PITCH = "+0Hz"
# Final loudness: af_nicole runs quiet, so lift her with gain plus a
# limiter -- loud without ever clipping into distortion.
KOKORO_GAIN = 1.6
TTS_KOKORO_VOICE = "af_nicole"  # her voice
TTS_KOKORO_SPEED = 1.1  # just a touch brisk; 1.0 is default
TTS_KOKORO_MODEL = BASE_DIR / "models" / "kokoro-v1.0.onnx"
TTS_KOKORO_VOICES = BASE_DIR / "models" / "voices-v1.0.bin"
TTS_MAX_CHARS = 600  # replies are cut to this before speaking

# Tool-call preview length shown in the terminal UI.
TUI_TOOL_PREVIEW_CHARS = 1200
