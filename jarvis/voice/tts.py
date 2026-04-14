"""Text-to-speech using Piper."""

import io
import os
import wave
import numpy as np
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from jarvis.utils.logger import get_logger

logger = get_logger("voice.tts")


@dataclass
class TTSConfig:
    voice_dir: str = "./voices"
    voice: str = "en_US-lessac-medium"


class TextToSpeech:
    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self.voice = None
        self._load_voice()

    def _load_voice(self):
        try:
            from piper import PiperVoice

            voice_path = Path(self.config.voice_dir) / f"{self.config.voice}.onnx"

            if not voice_path.exists():
                logger.warning(f"Voice model not found: {voice_path}")
                return

            self.voice = PiperVoice.load(str(voice_path))
            logger.info(f"Loaded voice: {self.config.voice}")

        except ImportError:
            logger.warning("piper-tts not installed. Run: pip install piper-tts")
        except Exception as e:
            logger.error(f"Failed to load voice: {e}")

    def is_available(self) -> bool:
        return self.voice is not None

    def speak(self, text: str, play: bool = True) -> Optional[bytes]:
        audio = self.text_to_speech(text)

        if audio and play:
            self._play_audio(audio)

        return audio

    def text_to_speech(self, text: str) -> Optional[bytes]:
        if not self.is_available():
            logger.warning("TTS not available")
            return None

        try:
            buffer = io.BytesIO()

            with wave.open(buffer, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(22050)
                self.voice.synthesize_wav(text, wf)

            return buffer.getvalue()

        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None

    def _play_audio(self, audio_data: bytes):
        try:
            import sounddevice as sd
            import scipy.io.wavfile as wavfile

            buffer = io.BytesIO(audio_data)
            sample_rate, audio = wavfile.read(buffer)

            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            elif len(audio.shape) > 1:
                audio = audio[:, 0]

            sd.play(audio, sample_rate)
            sd.wait()

        except Exception as e:
            logger.error(f"Audio playback error: {e}")

    def list_voices(self) -> list[dict]:
        voice_dir = Path(self.config.voice_dir)
        if not voice_dir.exists():
            return []

        voices = []
        for model_file in voice_dir.glob("*.onnx"):
            voice_name = model_file.stem
            voices.append(
                {
                    "name": voice_name,
                    "model": str(model_file),
                }
            )

        return voices
