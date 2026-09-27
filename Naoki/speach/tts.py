import queue
import re
import threading
import time

import numpy as np
import sounddevice as sd
import soundfile as sf
from kokoro_onnx import SAMPLE_RATE, Kokoro

from config import (
    TTS_LANG,
    TTS_MAX_CHARS,
    TTS_MODEL,
    TTS_OUT_DIR,
    TTS_SPEED,
    TTS_VOICE,
    TTS_VOICES,
)

# kokoro-onnx create() renders a whole string at once, so for streaming
# playback we split into sentences and synthesize sentence-by-sentence.
# One shared instance: model load is ~300MB, do it once.
_KOKORO: Kokoro | None = None
_KOKORO_LOCK = threading.Lock()


def _get_kokoro() -> Kokoro:
    global _KOKORO
    with _KOKORO_LOCK:  # two threads calling speak at once must not build twice
        if _KOKORO is None:
            _KOKORO = Kokoro(str(TTS_MODEL), str(TTS_VOICES))
        return _KOKORO


_MD_PATTERNS = (
    (re.compile(r"```.*?```", re.DOTALL), " "),  # fenced code blocks
    (re.compile(r"`([^`]*)`"), r"\1"),  # `inline code`
    (re.compile(r"!\[([^\]]*)\]\([^)]*\)"), r"\1"),  # ![img](src)
    (re.compile(r"\[([^\]]+)\]\([^)]*\)"), r"\1"),  # [text](url)
    (re.compile(r"https?://\S+"), " "),  # bare urls
    (re.compile(r"^\s{0,3}#{1,6}\s*", re.MULTILINE), ""),  # headings
    (re.compile(r"^\s{0,3}[-*+]\s+", re.MULTILINE), ""),  # bullets
    (re.compile(r"^\s{0,3}\d+\.\s+", re.MULTILINE), ""),  # ordered list markers
    (re.compile(r"[*_~]{1,3}"), ""),  # bold/italic/strike markers
    (re.compile(r"^\s{0,3}>\s?", re.MULTILINE), ""),  # block quotes
    (re.compile(r"\|"), " "),  # table pipes
    (re.compile(r"^[-=]{3,}$", re.MULTILINE), " "),  # rules
    (re.compile(r"[*#`_~|>]"), ""),  # any stragglers
)


def clean_for_speech(text: str) -> str:
    """Strip markdown so TTS doesn't read punctuation as words.

    Without this, '**directory**' is spoken as "asterisk asterisk directory".
    """
    out = text
    for pattern, repl in _MD_PATTERNS:
        out = pattern.sub(repl, out)
    out = re.sub(r"[ \t]{2,}", " ", out)  # collapse spacing
    out = re.sub(r"\n{2,}", ". ", out)  # paragraph break reads as a pause
    return out.replace("\n", ". ").strip()


def _split_sentences(text: str, max_chars: int = 150) -> list[str]:
    """Split into playable chunks: sentences first, then long ones on clauses.

    kokoro-onnx create() renders a whole string at once, so chunk size sets
    time-to-first-audio. Clauses keep chunks short without new dependencies.
    """
    sentences = [
        p.strip()
        for p in re.split(r"(?<=[.!?])\s+|\n+", text.strip())
        if p.strip()
    ]
    chunks: list[str] = []
    for sent in sentences:
        if len(sent) <= max_chars:
            chunks.append(sent)
            continue
        parts = [
            p.strip()
            for p in re.split(r"(?<=[;,:\u2014\u2013])\s+", sent)
            if p.strip()
        ]
        chunks.extend(parts or [sent])
    return chunks


def speak_streaming(text: str, voice: str = TTS_VOICE, save: bool = False) -> str | None:
    """Synthesize with kokoro-onnx and play in real time (producer/consumer).

    Returns the wav path when save=True, else None.
    """
    text = clean_for_speech(text or "").strip()[:TTS_MAX_CHARS]
    if not text:
        return None

    kokoro = _get_kokoro()

    # Bounded buffer: if synthesis outruns playback, put() blocks at 10
    # chunks instead of growing memory forever.
    q: queue.Queue = queue.Queue(maxsize=10)
    saved: list[np.ndarray] = []

    def producer() -> None:
        # Runs in background: synthesis is slow (model forward pass),
        # so push each sentence the moment it is rendered.
        try:
            for sent in _split_sentences(text):
                samples, _sr = kokoro.create(
                    sent, voice=voice, speed=TTS_SPEED, lang=TTS_LANG
                )
                chunk = np.asarray(samples, dtype=np.float32).reshape(-1)
                if save:
                    saved.append(chunk)
                q.put(chunk)  # blocks if queue full (playback is slower) — backpressure
        except (OSError, ValueError, RuntimeError) as e:
            print(f"[tts] synthesis error: {type(e).__name__}: {e}")
        finally:
            q.put(None)  # SENTINEL: tells consumer "no more chunks coming"

    t = threading.Thread(target=producer, name="kokoro-producer", daemon=True)
    t.start()

    # Consumer runs on THIS thread: pull chunks and play them in order.
    # q.get() blocks when empty (synthesis slower than playback), so we
    # simply wait instead of erroring or playing silence.
    try:
        with sd.OutputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32"
        ) as stream:
            while True:
                chunk = q.get()  # blocks here if producer hasn't delivered yet
                if chunk is None:  # sentinel -> generation finished, all played
                    break
                stream.write(
                    chunk
                )  # blocks here if sound card is busy — natural pacing
    except KeyboardInterrupt:
        print("\n[tts] interrupted")
    finally:
        # Daemon thread + sentinel guarantee: producer already finished or will
        # exit on its own; join so we don't return while it still holds the model.
        # Timeout avoids hanging forever if synthesis itself wedges.
        t.join(timeout=60)
        # Drain leftovers so a second speak_streaming() call starts clean.
        try:
            while not q.empty():
                q.get_nowait()
        except queue.Empty:
            pass

    if save and saved:
        TTS_OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = TTS_OUT_DIR / f"tts_{int(time.time() * 1000)}.wav"
        try:
            sf.write(str(out), np.concatenate(saved), SAMPLE_RATE)
            return str(out)
        except (OSError, ValueError, RuntimeError) as e:
            print(f"[tts] save error: {type(e).__name__}: {e}")
            return None
    return None
