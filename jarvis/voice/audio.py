"""Audio utilities for voice interface."""

import io
import wave
import numpy as np
from typing import Optional, Generator
from dataclasses import dataclass

try:
    import pyaudio

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

from jarvis.utils.logger import get_logger

logger = get_logger("voice.audio")


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    format_size: int = 2
    silence_threshold: int = 500
    silence_duration: float = 0.5


class AudioCapture:
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.audio: Optional["pyaudio.PyAudio"] = None
        self.stream = None

        if PYAUDIO_AVAILABLE:
            self.audio = pyaudio.PyAudio()
        else:
            logger.warning("PyAudio not available. Install with: pip install pyaudio")

    def is_available(self) -> bool:
        return self.audio is not None

    def list_devices(self) -> list[dict]:
        if not self.audio:
            return []

        devices = []
        for i in range(self.audio.get_device_count()):
            try:
                info = self.audio.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    devices.append(
                        {
                            "index": i,
                            "name": info["name"],
                            "channels": info["maxInputChannels"],
                            "sample_rate": int(info["defaultSampleRate"]),
                        }
                    )
            except Exception:
                continue
        return devices

    def start_stream(self):
        if not self.audio:
            raise RuntimeError("PyAudio not available")

        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size,
        )
        return self.stream

    def stop_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def read_chunk(self) -> np.ndarray:
        if not self.stream:
            raise RuntimeError("Stream not started")

        data = self.stream.read(self.config.chunk_size, exception_on_overflow=False)
        audio = np.frombuffer(data, dtype=np.int16)
        return audio.astype(np.float32) / 32768.0

    def record_until_silence(
        self, max_duration: float = 30.0, silence_timeout: float = 2.0
    ) -> np.ndarray:
        if not self.audio:
            raise RuntimeError("PyAudio not available")

        self.start_stream()

        frames = []
        max_frames = int(
            self.config.sample_rate / self.config.chunk_size * max_duration
        )
        max_silent_frames = int(
            silence_timeout * self.config.sample_rate / self.config.chunk_size
        )

        silent_frames = 0
        frame_count = 0
        speaking = False

        try:
            while frame_count < max_frames:
                data = self.stream.read(
                    self.config.chunk_size, exception_on_overflow=False
                )
                audio = np.frombuffer(data, dtype=np.int16)
                frames.append(data)

                mean_amplitude = np.abs(audio).mean()

                if mean_amplitude < self.config.silence_threshold:
                    silent_frames += 1
                    if speaking and silent_frames > max_silent_frames:
                        break
                else:
                    silent_frames = 0
                    speaking = True

                frame_count += 1
        finally:
            self.stop_stream()

        audio_data = b"".join(frames)
        audio_float = np.frombuffer(audio_data, dtype=np.int16)
        return audio_float.astype(np.float32) / 32768.0

    def close(self):
        self.stop_stream()
        if self.audio:
            self.audio.terminate()
            self.audio = None


class AudioProcessor:
    @staticmethod
    def preprocess(audio: np.ndarray, target_sample_rate: int = 16000) -> np.ndarray:
        audio = audio / np.max(np.abs(audio) + 1e-10)
        return audio

    @staticmethod
    def trim_silence(audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        energy = np.abs(audio)
        nonzero = np.where(energy > threshold)[0]

        if len(nonzero) == 0:
            return audio

        return audio[nonzero[0] : nonzero[-1] + 1]

    @staticmethod
    def normalize(audio: np.ndarray) -> np.ndarray:
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio

    @staticmethod
    def resample(audio: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
        if orig_rate == target_rate:
            return audio

        duration = len(audio) / orig_rate
        target_length = int(duration * target_rate)
        indices = np.linspace(0, len(audio) - 1, target_length)
        return np.interp(indices, np.arange(len(audio)), audio)

    @staticmethod
    def is_speech(audio: np.ndarray, threshold: float = 0.02) -> bool:
        return np.abs(audio).mean() > threshold


def audio_to_wav_bytes(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
    audio_int16 = (audio * 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

    return buffer.getvalue()


def load_wav(audio_bytes: bytes) -> np.ndarray:
    buffer = io.BytesIO(audio_bytes)
    with wave.open(buffer, "rb") as wf:
        sample_rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)
        return audio.astype(np.float32) / 32768.0, sample_rate
