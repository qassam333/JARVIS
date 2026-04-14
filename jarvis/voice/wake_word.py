"""Wake word detection."""

import threading
import time
import numpy as np
from typing import Callable, Optional, List
from dataclasses import dataclass, field

from jarvis.utils.logger import get_logger

logger = get_logger("voice.wake_word")

PORCUPINE_AVAILABLE = False
try:
    import pvporcupine

    PORCUPINE_AVAILABLE = True
except ImportError:
    logger.warning("Porcupine not installed. Run: pip install pvporcupine")


@dataclass
class WakeWordConfig:
    engine: str = "simple"
    keywords: List[str] = field(default_factory=lambda: ["hey gg", "gg", "hey jarvis", "jarvis", "hey jarvi", "jarvi"])
    sensitivity: float = 0.5
    porcupine_access_key: Optional[str] = None
    sample_rate: int = 16000
    audio_gain: float = 1.0


class WakeWordDetector:
    def __init__(self, config: Optional[WakeWordConfig] = None):
        self.config = config or WakeWordConfig()
        self.running = False
        self.callback: Optional[Callable] = None
        self._thread: Optional[threading.Thread] = None

        self._setup_engine()

    def _setup_engine(self):
        if self.config.engine == "porcupine" and PORCUPINE_AVAILABLE:
            self._setup_porcupine()
        else:
            self._setup_simple()

    def _setup_porcupine(self):
        if not self.config.porcupine_access_key:
            logger.warning(
                "Porcupine access key not provided, falling back to simple detection"
            )
            self._setup_simple()
            return

        try:
            keywords = [kw.replace("hey ", "").strip() for kw in self.config.keywords]

            self.porcupine = pvporcupine.create(
                access_key=self.config.porcupine_access_key,
                keywords=keywords,
                sensitivities=[self.config.sensitivity] * len(keywords),
            )

            self.engine = "porcupine"
            logger.info(f"Porcupine wake word engine initialized for: {keywords}")

        except Exception as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            self._setup_simple()

    def _setup_simple(self):
        self.engine = "simple"
        logger.info("Simple wake word detection initialized")
        logger.info("Keywords: " + ", ".join(self.config.keywords))

    def is_available(self) -> bool:
        return True

    def on_wake_word(self, callback: Callable):
        self.callback = callback

    def start(self, audio_capture):
        if self.running:
            return

        self.running = True
        self.audio_capture = audio_capture

        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

        logger.info("Wake word detection started")

    def stop(self):
        self.running = False

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        logger.info("Wake word detection stopped")

    def _listen_loop(self):
        if self.engine == "porcupine":
            self._porcupine_loop()
        else:
            self._simple_loop()

    def _porcupine_loop(self):
        stream = self.audio_capture.start_stream()

        try:
            while self.running:
                pcm = self.audio_capture.read_chunk()
                pcm_int16 = (pcm * 32767 * self.config.audio_gain).astype(np.int16)
                pcm_bytes = pcm_int16.tobytes()

                if len(pcm_bytes) >= self.porcupine.frame_length * 2:
                    frame = pcm_bytes[: self.porcupine.frame_length * 2]
                    keyword_index = self.porcupine.process(frame)

                    if keyword_index >= 0:
                        self._trigger()
                        time.sleep(0.5)

        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
        finally:
            self.audio_capture.stop_stream()

    def _simple_loop(self):
        from jarvis.voice.stt import SpeechToText

        stt = SpeechToText()

        if not stt.is_available():
            logger.error("STT not available for simple wake word detection")
            return

        stream = self.audio_capture.start_stream()
        silence_threshold = 500
        speech_threshold = 1000
        max_silent_chunks = 15
        min_speech_chunks = 2

        buffer = []
        silent_chunks = 0
        speech_chunks = 0

        try:
            while self.running:
                pcm = self.audio_capture.read_chunk()
                amplitude = np.abs(pcm * 32768).mean()

                if amplitude > speech_threshold:
                    buffer.append(pcm)
                    speech_chunks += 1
                    silent_chunks = 0
                elif amplitude < silence_threshold:
                    if speech_chunks >= min_speech_chunks:
                        buffer.append(pcm)
                        audio = np.concatenate(buffer)

                        text = stt.transcribe(audio).lower()
                        if self._check_keywords(text):
                            self._trigger()
                            time.sleep(0.5)

                        buffer = []
                        speech_chunks = 0
                    else:
                        buffer = []
                        speech_chunks = 0
                else:
                    silent_chunks += 1
                    if silent_chunks < max_silent_chunks and speech_chunks > 0:
                        buffer.append(pcm)
                    else:
                        buffer = []
                        speech_chunks = 0

        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
        finally:
            self.audio_capture.stop_stream()

    def _check_keywords(self, text: str) -> bool:
        # Strip punctuation completely since Whisper often outputs "G.G." or "G, G!"
        import re
        text_clean = re.sub(r'[^\w\s]', '', text.lower()).strip()

        for keyword in self.config.keywords:
            keyword_clean = re.sub(r'[^\w\s]', '', keyword.lower()).strip()

            # Handle edge cases where whisper separates letters like "g g" instead of "gg"
            if keyword_clean in text_clean or keyword_clean.replace(" ", "") in text_clean.replace(" ", ""):
                return True

            keywords_split = keyword_clean.split()
            if all(kw in text_clean for kw in keywords_split):
                return True

        return False

    def _trigger(self):
        logger.info("Wake word detected!")

        if self.callback:
            self.callback()
        else:
            logger.warning("No callback set for wake word detection")


class PushToTalk:
    def __init__(self, audio_capture):
        self.audio_capture = audio_capture
        self.active = False

    def is_available(self) -> bool:
        return self.audio_capture.is_available()

    def listen(self, timeout: float = 30.0) -> np.ndarray:
        logger.info("Push-to-talk: listening...")
        audio = self.audio_capture.record_until_silence(
            max_duration=timeout, silence_timeout=2.0
        )
        logger.info("Push-to-talk: recording complete")
        return audio


def create_wake_word_detector(
    config: Optional[WakeWordConfig] = None,
) -> WakeWordDetector:
    return WakeWordDetector(config)
