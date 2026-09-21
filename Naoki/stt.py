"""Speech to text for Naoki's /talk command.

arecord captures from the default mic (no Python audio deps needed),
faster-whisper transcribes fully offline in English and Hindi. The
whisper model downloads itself on first use (~500MB for "small") and
is cached after that. Everything raises RuntimeError with a human
message on failure -- the TUI shows it and carries on.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from config import STT_MAX_SECONDS, STT_MODEL


def record(seconds: int) -> Path:
    """Capture `seconds` of mic audio to a temp wav. Returns its path."""
    if shutil.which("arecord") is None:
        raise RuntimeError("arecord not found (install alsa-utils to use /talk)")
    if not 1 <= seconds <= STT_MAX_SECONDS:
        raise RuntimeError(f"record 1-{STT_MAX_SECONDS} seconds, got {seconds}")
    wav = Path(tempfile.mkdtemp(prefix="naoki_stt_")) / "mic.wav"
    try:
        subprocess.run(
            ["arecord", "-q", "-d", str(seconds), "-f", "S16_LE",
             "-r", "16000", "-c", "1", str(wav)],
            check=True,
            timeout=seconds + 15,
        )
    except subprocess.CalledProcessError:
        raise RuntimeError("mic recording failed -- is a microphone plugged in?")
    if not wav.is_file() or wav.stat().st_size < 1000:
        raise RuntimeError("captured silence -- check the mic and try again")
    return wav


def transcribe(wav: Path) -> str:
    """Transcribe a wav file (any language Whisper knows). Returns text."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError(
            "faster-whisper not installed "
            "(uv pip install --python ../ml_shit/bin/python faster-whisper)"
        )
    model = WhisperModel(STT_MODEL, compute_type="int8")  # fast on CPU, no GPU needed
    segments, _info = model.transcribe(str(wav))
    text = " ".join(seg.text for seg in segments).strip()
    if not text:
        raise RuntimeError("couldn't make out any words -- try again, closer to the mic")
    return text


def listen(seconds: int) -> str:
    """Record `seconds` from the mic and return what was said."""
    wav = record(seconds)
    try:
        return transcribe(wav)
    finally:
        try:
            wav.unlink()
            wav.parent.rmdir()
        except OSError:
            pass
