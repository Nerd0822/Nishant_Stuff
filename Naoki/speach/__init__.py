"""Speech package: streaming TTS core + blocking STT."""

from .stt import listen_once
from .tts import speak_streaming

__all__ = ["listen_once", "speak_streaming"]
