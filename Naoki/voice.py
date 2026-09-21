"""Text to speech for Naoki. Kokoro only.

speak() cleans the reply, splits mood spans (*stress*, _whisper_,
**excited**), synthesizes with Kokoro-82M, bends each segment to its
mood with ffmpeg, joins them gap-free, and plays the result. Returns
"kokoro" on success, None on failure (then silence). Edge/flite
engines below are dormant spares, selectable via /voice.
"""

import importlib.util
import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

from config import (
    TTS_EDGE_PITCH,
    TTS_EDGE_RATE,
    TTS_EDGE_VOICE,
    KOKORO_GAIN,
    TTS_KOKORO_SPEED,
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


def _split_emphasis(text: str) -> list[tuple[str, str]]:
    """Split mood spans out. Returns (segment, mood) pairs, mood one of
    plain / stress (*...*) / whisper (_..._) / excited (**...**).

    Unbalanced markers stay literal (cleaned away later), so model
    typos degrade to plain speech instead of errors. Underscore spans
    need a space inside so snake_case never splits.
    """
    token = "\x00"
    text = re.sub(r"\*\*(.+?)\*\*", rf"{token}E{token}\1{token}", text)
    text = re.sub(r"\*([^*]+?)\*", rf"{token}S{token}\1{token}", text)
    text = re.sub(r"_([^_\n]* [^_\n]*)_", rf"{token}W{token}\1{token}", text)
    out = []
    pending_mood = "plain"
    for chunk in text.split(token):
        if not chunk:
            continue
        if chunk in "ESW" and len(chunk) == 1:
            pending_mood = {"E": "excited", "S": "stress", "W": "whisper"}[chunk]
        else:
            if chunk.strip():
                out.append((chunk, pending_mood))
            pending_mood = "plain"
    return out


# Solo syntheses carry padded silence at both ends; trimming every
# part before joining is what keeps multi-mood replies gap-free.
_TRIM_AF = (
    "silenceremove=start_periods=1:start_duration=0.08:"
    "start_threshold=-50dB,areverse,silenceremove=start_periods=1:"
    "start_duration=0.08:start_threshold=-50dB,areverse"
)


def _join_segments(
    items: list[tuple[Path, str | None]],
    out_wav: Path,
    final_af: str | None = None,
) -> None:
    """Join audio parts into one wav. Each item is (file, ffmpeg -af or
    None) applied to that part first. Always re-encodes -- concat-copy
    of MP3s clicks at the seams."""
    tmpdir = out_wav.parent
    fixed = []
    for i, (src, af) in enumerate(items):
        dst = tmpdir / f"j{i}.wav"
        command = ["ffmpeg", "-y", "-loglevel", "quiet", "-i", str(src)]
        if af:
            command += ["-af", af]
        command += [str(dst)]
        subprocess.run(command, check=True, capture_output=True, timeout=120)
        fixed.append(dst)
    if len(fixed) == 1 and not final_af:
        shutil.copy2(fixed[0], out_wav)
        return
    listing = tmpdir / "parts.txt"
    listing.write_text(
        "".join(f"file '{p}'\n" for p in fixed), encoding="utf-8"
    )
    command = ["ffmpeg", "-y", "-loglevel", "quiet", "-f", "concat",
               "-safe", "0", "-i", str(listing)]
    if final_af:
        command += ["-af", final_af]
    command += [str(out_wav)]
    subprocess.run(command, check=True, capture_output=True, timeout=120)


def _synthesize_flite(text: str, wav_path: Path) -> bool:
    text = _clean_for_speech(text)
    if not text:
        return False
    subprocess.run(
        ["flite", "-voice", TTS_VOICE, "-o", str(wav_path), "-t", text],
        check=True,
        capture_output=True,
        timeout=120,
    )
    return True


def _synthesize_edge(text: str, wav_path: Path) -> bool:
    """Microsoft neural voices via the edge-tts CLI (needs internet).

    *asterisk* spans are spoken stressed: slower and louder, then
    joined seamlessly. Plain text takes the fast single-shot path.
    """
    if shutil.which("edge-tts") is None:
        _warn_once("[tts] edge-tts not installed")
        return False
    if shutil.which("ffmpeg") is None:
        _warn_once("[tts] ffmpeg needed for audio joins")
        return False

    segments = [
        (_clean_for_speech(part), mood)
        for part, mood in _split_emphasis(text)
    ]
    segments = [(part, mood) for part, mood in segments if part]
    if not segments:
        return False
    voice_name = TTS_EDGE_VOICE  # English voice, always -- no Hindi TTS

    # Mood to edge-tts prosody. All three are rate/pitch/volume --
    # the only levers the engine has. No laughter/sighs: physics.
    MOODS = {
        "plain": {},
        "stress": {"rate": "-15%", "volume": "+20%"},
        "whisper": {"rate": "-10%", "volume": "-30%", "pitch": "-5Hz"},
        "excited": {"rate": "+12%", "volume": "+10%", "pitch": "+5Hz"},
    }

    def _speak_one(part: str, mood: str, dest: Path) -> None:
        # NOTE: --rate=-15% (equals form): a bare "-15%" looks like a
        # flag to argparse and the call dies.
        flags = {"rate": TTS_EDGE_RATE, "pitch": TTS_EDGE_PITCH}
        flags.update(MOODS.get(mood, {}))
        command = [
            "edge-tts",
            f"--voice={voice_name}",
            f"--rate={flags['rate']}",
            f"--pitch={flags['pitch']}",
            "--text",
            part,
            f"--write-media={dest}",
        ]
        if "volume" in flags:
            command += [f"--volume={flags['volume']}"]
        subprocess.run(
            command, check=True, capture_output=True, timeout=120
        )

    tmpdir = Path(tempfile.mkdtemp(prefix="naoki_edge_"))
    try:
        items = []
        for i, (part, mood) in enumerate(segments):
            raw = tmpdir / f"seg{i}.mp3"
            _speak_one(part, mood, raw)
            items.append((raw, _TRIM_AF))
        _join_segments(items, wav_path)
        return True
    except subprocess.CalledProcessError:
        _warn_once("[tts] edge-tts call failed (offline?)")
        return False
    finally:
        import shutil as _shutil

        _shutil.rmtree(tmpdir, ignore_errors=True)


def _get_kokoro():
    """Load the Kokoro model once and keep it in memory."""
    global _kokoro_model
    if _kokoro_model is None:
        from kokoro_onnx import Kokoro  # lazy import: optional dependency

        _kokoro_model = Kokoro(str(TTS_KOKORO_MODEL), str(TTS_KOKORO_VOICES))
    return _kokoro_model


def _synthesize_kokoro(text: str, wav_path: Path) -> bool:
    """Kokoro 82M via onnxruntime (offline, CPU friendly).

    Moods survive the engine swap: each segment synthesizes neutrally,
    then ffmpeg bends it (tempo/volume per mood) before joining. Slower
    than edge flags, same audible effect.
    """
    try:
        import soundfile as sf  # optional dependency, only for writing the wav
    except ImportError:
        _warn_once(
            "[tts] kokoro-onnx/soundfile not installed "
            "(uv pip install kokoro-onnx soundfile)"
        )
        return False
    if not (TTS_KOKORO_MODEL.exists() and TTS_KOKORO_VOICES.exists()):
        _warn_once(
            f"[tts] kokoro model files missing in {TTS_KOKORO_MODEL.parent}"
        )
        return False

    segments = [
        (_clean_for_speech(part), mood)
        for part, mood in _split_emphasis(text)
    ]
    # Kokoro has no Hindi: Devanagari would come out as garbage
    # phonemes, so drop those runs (display keeps them, speech skips).
    segments = [
        (re.sub(r"[\u0900-\u097F]+", " ", part).strip(), mood)
        for part, mood in segments
    ]
    segments = [(part, mood) for part, mood in segments if part]
    if not segments:
        return False

    MOOD_FILTERS = {
        "plain": _TRIM_AF,
        "stress": f"{_TRIM_AF},atempo=0.85,volume=1.4",
        "whisper": f"{_TRIM_AF},atempo=0.9,volume=0.5",
        "excited": f"{_TRIM_AF},atempo=1.12,volume=1.2",
    }
    tmpdir = Path(tempfile.mkdtemp(prefix="naoki_kokoro_"))
    try:
        model = _get_kokoro()
        items = []
        for i, (part, mood) in enumerate(segments):
            samples, sample_rate = model.create(
                part, voice=TTS_KOKORO_VOICE, speed=TTS_KOKORO_SPEED, lang="en-us"
            )
            raw = tmpdir / f"seg{i}.wav"
            sf.write(str(raw), samples, sample_rate)
            items.append((raw, MOOD_FILTERS.get(mood)))
        _join_segments(
            items, wav_path,
            final_af=f"volume={KOKORO_GAIN},alimiter=limit=0.95",
        )
        return True
    except Exception as exc:
        _warn_once(f"[tts] kokoro failed: {type(exc).__name__}: {exc}")
        return False
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


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
    """Kokoro only, by choice: her voice, offline, no cloud, no robot.

    Returns "kokoro" on success, None on failure (then silence -- there
    is deliberately no fallback chain anymore).
    """
    try:
        if _ENGINES["kokoro"](text, wav_path):
            return "kokoro"
    except Exception as exc:
        _warn_once(f"[tts] {type(exc).__name__}: {exc}")
    return None


def _play_wav(wav_path: Path) -> None:
    """Play one wav file, blocking. Best-effort."""
    player = next((name for name in _PLAYERS if shutil.which(name)), None)
    if player is None:
        return
    if player == "ffplay":
        command = [
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(wav_path),
        ]
    else:
        command = [player, str(wav_path)]
    subprocess.run(command, check=False, capture_output=True, timeout=300)


def _split_sentences(text: str) -> list[str]:
    """Split a reply into speakable sentences (keeps the punctuation)."""
    parts = re.split(r"(?<=[.!?])\s+", str(text).strip())
    return [p for p in parts if p.strip()]


def speak(text: str) -> str | None:
    """Say `text` out loud (blocking); returns the engine that spoke, or None.

    Long replies stream sentence by sentence: the first sentence plays
    while the next synthesizes (one-sentence lookahead), so she starts
    talking in ~3s instead of after the whole reply renders.
    """
    if not ENABLED or not str(text).strip():
        return None

    sentences = _split_sentences(text)
    if len(sentences) < 2 or len(str(text)) < 200:
        return _speak_single(str(text))

    from concurrent.futures import ThreadPoolExecutor

    tmpdir = Path(tempfile.mkdtemp(prefix="naoki_stream_"))
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(_synth_file, sentences[0], tmpdir / "s0.wav")
            played_any = False
            for i, sentence in enumerate(sentences[1:], 1):
                wav = pending.result()
                if wav is not None:
                    _play_wav(wav)
                    played_any = True
                pending = pool.submit(_synth_file, sentence, tmpdir / f"s{i}.wav")
            wav = pending.result()
            if wav is not None:
                _play_wav(wav)
                played_any = True
        return "kokoro" if played_any else None
    except (OSError, subprocess.SubprocessError):
        return None  # speech is best-effort; never break the assistant over audio
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _synth_file(text: str, dest: Path) -> Path | None:
    """Synthesize one chunk to `dest`. Path back, or None on failure."""
    try:
        if _synthesize(text, dest):
            return dest
    except Exception:
        pass
    return None


def _speak_single(text: str) -> str | None:
    """Classic path: one wav for short replies."""
    wav_path = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="naoki_tts_", suffix=".wav", delete=False
        ) as tmp:
            wav_path = Path(tmp.name)
        engine_used = _synthesize(text, wav_path)
        if engine_used is None:
            return None
        _play_wav(wav_path)
        return engine_used
    except (OSError, subprocess.SubprocessError):
        return None  # speech is best-effort; never break the assistant over audio
    finally:
        if wav_path is not None:
            wav_path.unlink(missing_ok=True)
