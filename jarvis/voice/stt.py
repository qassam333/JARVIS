"""Speech-to-text using Whisper."""

import numpy as np
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from jarvis.utils.logger import get_logger

logger = get_logger("voice.stt")

WHISPER_AVAILABLE = False
try:
    from faster_whisper import WhisperModel

    WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("faster-whisper not installed. Run: pip install faster-whisper")


@dataclass
class STTConfig:
    model_size: str = "base"
    language: Optional[str] = None


class SpeechToText:
    def __init__(self, config: Optional[STTConfig] = None):
        self.config = config or STTConfig()
        self.model = None

        if WHISPER_AVAILABLE:
            self._setup()

    def _setup(self):
        try:
            logger.info(f"Loading Whisper {self.config.model_size} model...")
            self.model = WhisperModel(
                self.config.model_size, device="cpu", compute_type="int8"
            )
            logger.info("Whisper model loaded")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")

    def is_available(self) -> bool:
        return self.model is not None

    def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> str:
        if not self.is_available():
            raise RuntimeError("STT not available")

        lang = language or self.config.language

        try:
            segments, info = self.model.transcribe(
                audio,
                language=lang,
                beam_size=5,
                best_of=5,
            )

            text = " ".join(segment.text for segment in segments)
            return text.strip()

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    def transcribe_file(self, audio_path: str, language: Optional[str] = None) -> str:
        if not self.is_available():
            raise RuntimeError("STT not available")

        lang = language or self.config.language

        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=lang,
            )

            text = " ".join(segment.text for segment in segments)
            return text.strip()

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
