"""Mic test: records a few seconds, shows the level, plays it back.

Usage:  ../ml_shit/bin/python mic_test.py [seconds, default 5]

Say something after "recording...". If the bar stays flat, the mic is
muted, unplugged, or the wrong device -- check pavucontrol. Pass
--transcribe to also run it through faster-whisper (proves the full
/talk chain without entering the TUI).
"""

import shutil
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

SECS = float(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1][0].isdigit() else 5
WANT_TRANSCRIBE = "--transcribe" in sys.argv


def need(binary: str) -> None:
    if shutil.which(binary) is None:
        sys.exit(f"missing '{binary}' -- cannot test the mic without it")


def peak_level(wav: Path) -> tuple[float, str]:
    """Peak mic level 0-100 plus an ASCII bar."""
    with wave.open(str(wav), "rb") as f:
        frames = f.readframes(f.getnframes())
        width = f.getsampwidth()
    fmt = {1: "b", 2: "h", 4: "i"}.get(width, "h")
    step = width
    peak = 0
    for i in range(0, len(frames) - step + 1, step):
        sample = abs(struct.unpack("<" + fmt, frames[i : i + step])[0])
        if sample > peak:
            peak = sample
    full_scale = float(2 ** (8 * width - 1))
    pct = min(100.0, peak / full_scale * 100)
    bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
    return pct, f"[{bar}] {pct:.0f}%"


def main() -> None:
    need("arecord")
    wav = Path(tempfile.mkdtemp(prefix="mic_test_")) / "test.wav"
    print(f"recording {SECS:g}s -- say something! ...")
    try:
        subprocess.run(
            ["arecord", "-q", "-d", str(int(SECS)), "-f", "S16_LE",
             "-r", "16000", "-c", "1", str(wav)],
            check=True,
            timeout=SECS + 15,
        )
    except subprocess.CalledProcessError:
        sys.exit("recording failed -- mic missing or busy (check pavucontrol)")
    kb = wav.stat().st_size // 1024
    pct, bar = peak_level(wav)
    print(f"captured {kb} KB, peak level: {bar}")
    if pct < 2:
        print("flat line -- mic is muted, unplugged, or the wrong input.")
    elif pct < 15:
        print("very quiet -- move closer or boost input volume.")
    else:
        print("levels look healthy.")

    player = next((p for p in ("paplay", "pw-play", "aplay") if shutil.which(p)), None)
    if player:
        print(f"playing back via {player}...")
        subprocess.run([player, str(wav)], check=False,
                       capture_output=True, timeout=60)
    else:
        print("no audio player found -- skipping playback.")

    if WANT_TRANSCRIBE:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import stt

        print("transcription:", stt.transcribe(wav))
    wav.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
