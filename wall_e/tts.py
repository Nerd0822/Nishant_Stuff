"""Kokoro text-to-speech for the assistant (offline, CPU).

One engine only: kokoro-onnx v1.0 with the `af_nicole` voice (voices-v1.0.bin
carries 54 of them; `/voice` lists the names). Speech is real time: the reply is
cut into sentence-sized pieces, each piece goes to the speakers through
sounddevice the moment it comes out of the model, and the next piece is already
being rendered while the current one plays. The first words are audible about a
second in, and a cancel never waits for more than the piece being spoken.

When sounddevice cannot open an output device the whole clip is rendered to a
wav file and handed to a system player instead.

`speak()` never raises on engine or audio problems -- it prints one warning and
stays silent -- but a Ctrl+C cancel is passed through to the caller. `stop()`
cuts playback short from any thread, and `shutdown()` drops the model so it
stops occupying RAM after the session ends.
"""

import asyncio
import contextlib
import importlib.util
import re
import shutil
import subprocess
import tempfile
import threading
import unicodedata
from pathlib import Path

from .config import (
    TTS_ENABLED,
    TTS_MAX_CHARS,
    TTS_MODEL,
    TTS_REALTIME,
    TTS_SPEED,
    TTS_VOICE,
    TTS_VOICES,
)

ENABLED = TTS_ENABLED
VOICE = TTS_VOICE
SAMPLE_RATE = 24000  # kokoro v1.0 output
_PLAYERS = ("paplay", "pw-play", "aplay", "ffplay")
_SLICE_SECONDS = 0.25  # how often playback looks for a cancel
_PIECE_CHARS = 120  # replies are rendered one sentence-sized piece at a time
_QUEUE_SIZE = 2  # pieces held ready while the current one is playing
_CANCEL_JOIN = 1.0  # seconds to wait for the pump after a cancel

# First letter of a voice name picks the phonemizer language (af_ -> en-us).
_LANGS = {
    "a": "en-us",
    "b": "en-gb",
    "e": "es",
    "f": "fr",
    "h": "hi",
    "i": "it",
    "j": "ja",
    "p": "pt-br",
    "z": "cmn",
}

_warned: set[str] = set()
_voice_names: list[str] | None = None
_model = None
_model_lock = threading.Lock()
_speak_lock = threading.Lock()
_stop = threading.Event()
_stream_ok: bool | None = None
_stream_failed = False


def set_enabled(enabled: bool) -> None:
    global ENABLED
    ENABLED = enabled


def set_voice(name: str) -> bool:
    """Switch voice live; False for names this model does not carry."""
    global VOICE
    name = name.strip().lower()
    if not name:
        return False
    names = available_voices()
    if names:
        if name not in names:
            return False
    elif not re.fullmatch(r"[a-z]{2}_[a-z0-9]+", name):
        return False
    VOICE = name
    return True


def available_voices() -> list[str]:
    """Every voice name in voices-v1.0.bin (54 for v1.0); [] if unreadable."""
    global _voice_names
    if _voice_names is None:
        try:
            import numpy as np

            with np.load(TTS_VOICES) as bundle:
                _voice_names = sorted(bundle.files)
        except Exception:
            _voice_names = []
    return list(_voice_names)


def stop() -> None:
    """Cut playback short (safe from any thread, safe while silent)."""
    _stop.set()


def shutdown() -> None:
    """Stop talking and drop the model so exit leaves no RAM behind."""
    global _model
    stop()
    with _model_lock:
        _model = None


def speak(text: str) -> str | None:
    """Say `text` out loud (blocking); returns "kokoro" when audio played.

    A Ctrl+C during playback is re-raised once the audio is torn down, so the
    caller can tell a cancel apart from a silent engine failure.
    """
    clean = _clean_for_speech(text)
    if not ENABLED or not clean:
        return None

    state = voice_status()
    broken = _missing(state)
    if broken:
        _warn_once(f"[tts] kokoro cannot speak ({', '.join(broken)} missing) -- silent")
        return None

    with _speak_lock:
        _stop.clear()
        try:
            model = _load_model()
            if TTS_REALTIME and state["sounddevice"]:
                played = _play_stream(clean, model)
                if not played and not _stop.is_set():
                    _note_stream_failure()
            else:
                played = _play_file(clean, model)
        except KeyboardInterrupt:
            stop()  # tell the pump to abort at its next slice
            raise
        except Exception as exc:
            _warn_once(f"[tts] kokoro failed: {type(exc).__name__}: {exc}")
            return None
        finally:
            _stop.clear()
    return "kokoro" if played else None


def _can_stream() -> bool:
    """True when sounddevice can open an output device on this machine."""
    global _stream_ok
    if _stream_failed:
        return False
    if _stream_ok is None:
        try:
            import sounddevice as sd

            sd.query_devices(kind="output")
            _stream_ok = True
        except Exception:
            _stream_ok = False
    return _stream_ok


def voice_status() -> dict[str, bool]:
    """Audio stack pieces, and whether each one is in place right now."""
    return {
        "kokoro-onnx": importlib.util.find_spec("kokoro_onnx") is not None,
        "model": TTS_MODEL.exists(),
        "voices": TTS_VOICES.exists(),
        "sounddevice": importlib.util.find_spec("sounddevice") is not None
        and _can_stream(),
        "soundfile": importlib.util.find_spec("soundfile") is not None,
        "player": any(shutil.which(name) for name in _PLAYERS),
    }


def _missing(state: dict[str, bool]) -> list[str]:
    """What is missing before kokoro can speak at all."""
    broken = [name for name in ("kokoro-onnx", "model", "voices") if not state[name]]
    if not state["sounddevice"]:
        if not state["player"]:
            broken.append("player")
        if not state["soundfile"]:
            broken.append("soundfile")
    return broken


def _warn_once(message: str) -> None:
    if message not in _warned:
        _warned.add(message)
        print(message)


def _note_stream_failure() -> None:
    """Realtime playback blew up: use the wav player for the rest of the run."""
    global _stream_failed
    if not _stream_failed:
        _stream_failed = True
        _warn_once("[tts] realtime playback failed -- playing wav files instead")


def _load_model():
    """Load Kokoro once, on first use (82M onnx, about a second warm)."""
    global _model
    with _model_lock:
        if _model is None:
            from kokoro_onnx import Kokoro

            _model = Kokoro(str(TTS_MODEL), str(TTS_VOICES))
        return _model


def _lang_for(voice: str) -> str:
    """Phonemizer language implied by the voice name (af_nicole -> en-us)."""
    return _LANGS.get(voice[:1], "en-us")


def _pieces(text: str) -> list[str]:
    """Sentence-sized pieces, so speech starts (and stops) without waiting.

    Kokoro can only render about 510 phonemes in one pass -- roughly a full
    reply -- so a long text is one big batch that takes seconds to finish.
    Cutting at sentence (then clause, then word) boundaries keeps every render
    short: first audio lands much sooner and a cancel never blocks on the whole
    answer.
    """
    pieces: list[str] = []
    for sentence in re.split(r"(?<=[.!?…])\s+", text):
        sentence = sentence.strip()
        while len(sentence) > _PIECE_CHARS:
            cut = max(sentence.rfind(mark, 0, _PIECE_CHARS) for mark in (",", ";", ":"))
            if cut <= 0:
                cut = sentence.rfind(" ", 0, _PIECE_CHARS)
            if cut <= 0:
                cut = _PIECE_CHARS
            pieces.append(sentence[: cut + 1].strip())
            sentence = sentence[cut + 1 :].strip()
        if sentence:
            pieces.append(sentence)
    return pieces


def _clean_for_speech(text: str) -> str:
    """Strip markdown so it is not read aloud, and cap the length."""
    text = re.sub(r"```.*?```", " code block omitted. ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_#>]+", "", text)
    # Drop emojis/symbols so TTS reads text cleanly; keep ASCII and unicode
    # letters/markers/numbers for non-English scripts.
    text = "".join(
        ch
        for ch in text
        if (ch.isascii() and (ch.isalnum() or ch.isspace() or ch in ".,!?;:'\"()-+/=%@&"))
        or (not ch.isascii() and unicodedata.category(ch)[0] in "LMN")
    )
    # An English voice would turn Devanagari into garbage phonemes: drop those
    # runs from speech (the printed reply keeps them).
    if _lang_for(VOICE) != "hi":
        text = re.sub(r"[\u0900-\u097F]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > TTS_MAX_CHARS:
        text = text[:TTS_MAX_CHARS].rsplit(" ", 1)[0] + " ..."
    return text


def _cancelled(abort: threading.Event) -> bool:
    """Latch a cancel for this call, so a later `_stop.clear()` cannot revive it."""
    if abort.is_set() or _stop.is_set():
        abort.set()
        return True
    return False


def _play_stream(text: str, model) -> bool:
    """Realtime playback: the next piece renders while the current one plays."""
    outcome: list[bool] = []
    abort = threading.Event()

    def worker() -> None:
        outcome.append(asyncio.run(_pump_stream(text, model, abort)))

    thread = threading.Thread(target=worker, name="wall-e-tts", daemon=True)
    thread.start()
    try:
        while thread.is_alive():
            thread.join(_SLICE_SECONDS)
            if _stop.is_set():
                # The pump aborts the stream on its own; do not hold the prompt
                # hostage for the piece the model is still finishing.
                abort.set()
                thread.join(_CANCEL_JOIN)
                break
    except KeyboardInterrupt:
        stop()
        abort.set()
        thread.join(_CANCEL_JOIN)
        raise
    return bool(outcome and outcome[0])


async def _pump_stream(text: str, model, abort: threading.Event) -> bool:
    """Render pieces ahead of playback and push each one straight to the DAC."""
    import sounddevice as sd

    queue: asyncio.Queue = asyncio.Queue(maxsize=_QUEUE_SIZE)

    async def render() -> None:
        """Synthesize piece by piece, so a cancel only waits for one piece."""
        try:
            for piece in _pieces(text):
                if _cancelled(abort):
                    return
                async for chunk in model.create_stream(
                    piece, voice=VOICE, speed=TTS_SPEED, lang=_lang_for(VOICE)
                ):
                    await queue.put(chunk)
        finally:
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(None)

    producer = asyncio.create_task(render())
    stream = None
    try:
        while True:
            if _cancelled(abort):
                return False
            item = await queue.get()
            if item is None:
                break
            samples, sample_rate = item
            if stream is None:
                stream = sd.RawOutputStream(
                    samplerate=sample_rate, channels=1, dtype="float32"
                )
                stream.start()
            raw = samples.astype("float32", copy=False)
            slice_size = max(1, int(sample_rate * _SLICE_SECONDS))
            for start in range(0, raw.size, slice_size):
                if _cancelled(abort):
                    return False
                stream.write(raw[start : start + slice_size].tobytes())
        return stream is not None
    finally:
        # Silence first: waiting for the abandoned render must not keep talking.
        if stream is not None:
            if abort.is_set():
                stream.abort(ignore_errors=True)  # drop the queue, cut the tail
            else:
                stream.stop(ignore_errors=True)  # let the buffered tail play out
            stream.close(ignore_errors=True)
        producer.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await producer


def _play_file(text: str, model) -> bool:
    """Fallback: render the whole clip, then hand a wav to a system player."""
    import soundfile as sf

    player = next((name for name in _PLAYERS if shutil.which(name)), None)
    if player is None:
        _warn_once(f"[tts] no audio player found ({', '.join(_PLAYERS)}) -- silent")
        return False

    samples, sample_rate = model.create(
        text, voice=VOICE, speed=TTS_SPEED, lang=_lang_for(VOICE)
    )
    with tempfile.NamedTemporaryFile(
        prefix="wall-e_tts_", suffix=".wav", delete=False
    ) as handle:
        wav_path = Path(handle.name)
    try:
        sf.write(str(wav_path), samples, sample_rate)
        command = [player, str(wav_path)]
        if player == "ffplay":
            command = [
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
                str(wav_path),
            ]
        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        try:
            while process.poll() is None:
                if _stop.wait(_SLICE_SECONDS):
                    process.terminate()
                    return False
            return True
        finally:
            if process.poll() is None:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
    finally:
        wav_path.unlink(missing_ok=True)
