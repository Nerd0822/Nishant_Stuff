"""Text to speech for Wall-e.

Engines (config.TTS_ENGINE): "flite" (installed, offline), "edge"
(pip install edge-tts, needs internet), "kokoro" (pip install kokoro-onnx
soundfile + model files in ./models). speak() never raises: the configured
engine falls back to flite, and silence is the last resort. On success it
returns the engine that actually spoke, so callers can show honest status.
"""

import importlib.util
import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

from config import (
    TTS_EDGE_VOICE,
    TTS_ENABLED,
    TTS_ENGINE,
    TTS_KOKORO_MODEL,
    TTS_KOKORO_VOICE,
    TTS_KOKORO_VOICES,
    TTS_MAX_CHARS,
    TTS_VOICE,
)

ENABLED = TTS_ENABLED
_PLAYERS = ("paplay", "pw-play", "aplay", "ffplay")  # all already installed
_warned = set()
_kokoro_model = None


def set_enabled(enabled: bool) -> None:
    global ENABLED
    ENABLED = enabled


def _warn_once(message: str) -> None:
    if message not in _warned:
        _warned.add(message)
        print(message)


def _clean_for_speech(text: str) -> str:
    """Strip markdown so it is not read aloud, and cap the length."""
    text = re.sub(r"```.*?```", " code block omitted. ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # [label](url) -> label
    text = re.sub(r"[*_#>]+", "", text)
    # Drop emojis/symbols/pictographs a small model may emit anyway: TTS
    # engines read them as literal names ("smiling face", "black star") or
    # beep over them. Kept: ASCII letters/digits/common punctuation, plus any
    # unicode letter/mark/number (covers Devanagari, accents, etc.).
    text = "".join(
        ch
        for ch in text
        if (ch.isascii() and (ch.isalnum() or ch.isspace() or ch in ".,!?;:'\"()-+/=%@&"))
        or (not ch.isascii() and unicodedata.category(ch)[0] in "LMN")
    )
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > TTS_MAX_CHARS:
        text = text[:TTS_MAX_CHARS].rsplit(" ", 1)[0] + " ..."
    return text


def _synthesize_flite(text: str, wav_path: Path) -> bool:
    subprocess.run(
        ["flite", "-voice", TTS_VOICE, "-o", str(wav_path), "-t", text],
        check=True,
        capture_output=True,
        timeout=120,
    )
    return True


def _synthesize_edge(text: str, wav_path: Path) -> bool:
    """Microsoft neural voices via the edge-tts CLI (needs internet)."""
    if shutil.which("edge-tts") is None:
        _warn_once(
            "[tts] edge-tts not installed (uv pip install edge-tts) -- using flite"
        )
        return False
    if shutil.which("ffmpeg") is None:
        _warn_once("[tts] ffmpeg needed to convert edge-tts audio -- using flite")
        return False

    with tempfile.NamedTemporaryFile(
        prefix="wall-e_edge_", suffix=".mp3", delete=False
    ) as tmp:
        mp3_path = Path(tmp.name)
    try:
        subprocess.run(
            [
                "edge-tts",
                "--voice",
                TTS_EDGE_VOICE,
                "--text",
                text,
                "--write-media",
                str(mp3_path),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "quiet", "-i", str(mp3_path), str(wav_path)],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return True
    except subprocess.CalledProcessError:
        _warn_once("[tts] edge-tts call failed (offline?) -- using flite")
        return False
    finally:
        mp3_path.unlink(missing_ok=True)


def _get_kokoro():
    """Load the Kokoro model once and keep it in memory."""
    global _kokoro_model
    if _kokoro_model is None:
        from kokoro_onnx import Kokoro  # lazy import: optional dependency

        _kokoro_model = Kokoro(str(TTS_KOKORO_MODEL), str(TTS_KOKORO_VOICES))
    return _kokoro_model


def _synthesize_kokoro(text: str, wav_path: Path) -> bool:
    """Kokoro 82M via onnxruntime (offline, CPU friendly)."""
    try:
        import soundfile as sf  # optional dependency, only for writing the wav
    except ImportError:
        _warn_once(
            "[tts] kokoro-onnx/soundfile not installed "
            "(uv pip install kokoro-onnx soundfile) -- using flite"
        )
        return False
    if not (TTS_KOKORO_MODEL.exists() and TTS_KOKORO_VOICES.exists()):
        _warn_once(
            f"[tts] kokoro model files missing in {TTS_KOKORO_MODEL.parent} -- using flite"
        )
        return False

    samples, sample_rate = _get_kokoro().create(
        text, voice=TTS_KOKORO_VOICE, speed=1.0, lang="en-us"
    )
    sf.write(str(wav_path), samples, sample_rate)
    return True


_ENGINES = {
    "flite": _synthesize_flite,
    "edge": _synthesize_edge,
    "kokoro": _synthesize_kokoro,
}

ENGINE_NAMES = tuple(_ENGINES)


def set_engine(name: str) -> bool:
    """Switch the active engine at runtime. Returns False for unknown names."""
    global TTS_ENGINE
    if name not in _ENGINES:
        return False
    TTS_ENGINE = name
    return True


def engine_status() -> dict[str, bool]:
    """Which engines are usable right now (binaries installed, model files present)."""
    return {
        "flite": shutil.which("flite") is not None,
        "edge": shutil.which("edge-tts") is not None
        and shutil.which("ffmpeg") is not None,
        "kokoro": (
            importlib.util.find_spec("kokoro_onnx") is not None
            and importlib.util.find_spec("soundfile") is not None
            and TTS_KOKORO_MODEL.exists()
            and TTS_KOKORO_VOICES.exists()
        ),
    }


def _synthesize(text: str, wav_path: Path) -> str | None:
    """Try the configured engine, then flite; returns the engine that spoke."""
    for engine_name in dict.fromkeys((TTS_ENGINE, "flite")):
        engine = _ENGINES.get(engine_name)
        if engine is None:
            _warn_once(f"[tts] unknown engine '{engine_name}' in config")
            continue
        try:
            if engine(text, wav_path):
                return engine_name
        except Exception as exc:
            _warn_once(f"[tts] {engine_name} failed: {type(exc).__name__}: {exc}")
    return None


def speak(text: str) -> str | None:
    """Say `text` out loud (blocking); returns the engine that spoke, or None."""
    clean = _clean_for_speech(text)
    if not ENABLED or not clean:
        return None

    wav_path = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="wall-e_tts_", suffix=".wav", delete=False
        ) as tmp:
            wav_path = Path(tmp.name)
        engine_used = _synthesize(clean, wav_path)
        if engine_used is None:
            return None
        player = next((name for name in _PLAYERS if shutil.which(name)), None)
        if player is None:
            return
        if player == "ffplay":
            command = [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-loglevel",
                "quiet",
                str(wav_path),
            ]
        else:
            command = [player, str(wav_path)]
        subprocess.run(command, check=False, capture_output=True, timeout=300)
        return engine_used
    except (OSError, subprocess.SubprocessError):
        return None  # speech is best-effort; never break the assistant over audio
    finally:
        if wav_path is not None:
            wav_path.unlink(missing_ok=True)
