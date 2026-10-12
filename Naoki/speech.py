"""Listening test for Supertonic 3 with persona lines.

Usage:  python supertonic_test.py            (M1 + F1..F5)
        python supertonic_test.py F2 F4      (only these voices)
Writes data/voice_test/supertonic/<voice>_<line>.wav
"""

import sys
import time
from pathlib import Path

from supertonic import TTS

OUT = Path(__file__).resolve().parent / "data" / "voice_test" / "supertonic"
SPEED = 0.95  # 0.7 slow ... 2.0 fast. A little slow sounds more deliberate.
STEPS = 8  # quality 5 (low) ... 12 (high). Lower it if generation is too slow.

# name: (language code, text)
LINES = {
    "en": (
        "en",
        "Come here, darling. <breath> You're late, and I don't like waiting. "
        "Sit down... and tell me who kept you away from me.",
    ),
    "hi": (
        "hi",
        "इधर आओ। <breath> आज तुम बहुत देर से आए हो, और मुझे इंतज़ार करना बिल्कुल पसंद नहीं। "
        "चुपचाप बैठो, और मुझे बताओ, किसने तुम्हें मुझसे दूर रखा?",
    ),
    # the accent trick: English words written in Devanagari, read with Hindi sounds
    "accent": (
        "hi",
        "कम हियर, डार्लिंग। <breath> यू आर लेट, एंड आई डोंट लाइक वेटिंग। "
        "सिट डाउन, एंड टेल मी हू केप्ट यू अवे फ्रॉम मी।",
    ),
    # Hindi with English words left in Latin letters
    "mix": (
        "hi",
        "आज तुम बहुत late हो गए, <sigh> मुझे बहुत tension हो रही थी। अब घर आओ, मेरी जान।",
    ),
}

tts = TTS(auto_download=True)
OUT.mkdir(parents=True, exist_ok=True)

for name in sys.argv[1:] or ["M1", "F1", "F2", "F3", "F4", "F5"]:
    style = tts.get_voice_style(voice_name=name)
    for key, (lang, text) in LINES.items():
        t = time.perf_counter()
        wav, duration = tts.synthesize(
            text, voice_style=style, total_steps=STEPS, speed=SPEED, lang=lang
        )
        took = time.perf_counter() - t
        tts.save_audio(wav, str(OUT / f"{name}_{key}.wav"))
        secs = float(duration)
        print(
            f"{name:3} {key:7} {secs:4.1f}s of audio in {took:4.1f}s  (x{secs / took:.1f} real time)"
        )
