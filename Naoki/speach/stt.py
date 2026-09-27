"""Blocking record-then-transcribe STT using sounddevice + faster-whisper.

Not simultaneous with the LLM: we record until silence, then transcribe.
That costs ~1-2s before the agent starts, in exchange for a much simpler
and far more reliable loop than a streaming ASR pipeline.
"""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import (
    STT_BLOCK,
    STT_CHANNELS,
    STT_COMPUTE_TYPE,
    STT_DEVICE,
    STT_MAX_SEC,
    STT_MODEL,
    STT_SAMPLE_RATE,
    STT_SILENCE_RMS,
    STT_SILENCE_SEC,
)

_MODEL: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _MODEL
    if _MODEL is None:  # lazy: first call pays the load cost, then it's cached
        _MODEL = WhisperModel(
            STT_MODEL, device=STT_DEVICE, compute_type=STT_COMPUTE_TYPE
        )
    return _MODEL


def _rms(block: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(block)))) if block.size else 0.0


def listen_once() -> str:
    """Record from mic until silence, then transcribe. Returns '' on silence/EOF."""
    blocks: list[np.ndarray] = []
    silence_run = 0.0
    recorded = 0.0
    silence_needed = int(STT_SILENCE_SEC * STT_SAMPLE_RATE / STT_BLOCK)

    try:
        with sd.InputStream(
            samplerate=STT_SAMPLE_RATE,
            channels=STT_CHANNELS,
            dtype="float32",
            blocksize=STT_BLOCK,
        ) as stream:
            while recorded < STT_MAX_SEC:
                data, _overflowed = stream.read(STT_BLOCK)
                mono = data.reshape(-1)  # flatten to 1-D; STT_CHANNELS=1 anyway
                blocks.append(mono.copy())
                recorded += STT_BLOCK / STT_SAMPLE_RATE

                if _rms(mono) < STT_SILENCE_RMS:
                    silence_run += 1
                    # Require some audio first, so we don't stop on open-mic silence.
                    if silence_run >= silence_needed and len(blocks) > silence_needed:
                        break
                else:
                    silence_run = 0
    except (OSError, ValueError, RuntimeError) as e:
        print(f"[stt] mic error: {type(e).__name__}: {e}")
        return ""

    if not blocks:
        return ""
    audio = np.concatenate(blocks)
    if _rms(audio) < STT_SILENCE_RMS:
        return ""  # nothing was said

    try:
        segments, _info = _get_model().transcribe(
            audio, language="en", vad_filter=True
        )
        text = " ".join(s.text.strip() for s in segments).strip()
    except (OSError, ValueError, RuntimeError) as e:
        print(f"[stt] transcribe error: {type(e).__name__}: {e}")
        return ""
    return text
