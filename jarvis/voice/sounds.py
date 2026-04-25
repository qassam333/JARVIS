"""Audio feedback sounds for voice interface.

Generates sine-wave beeps programmatically — no external sound files needed.
Uses sounddevice (already a dependency for TTS playback) for output.
"""

import numpy as np
from jarvis.utils.logger import get_logger

logger = get_logger("voice.sounds")

# Check for sounddevice availability
_SD_AVAILABLE = False
try:
    import sounddevice as sd
    _SD_AVAILABLE = True
except ImportError:
    logger.debug("sounddevice not available — audio cues disabled")


def _generate_tone(frequency: float, duration: float, sample_rate: int = 22050,
                   volume: float = 0.3) -> np.ndarray:
    """Generate a sine wave tone."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Apply envelope to avoid clicks
    envelope = np.ones_like(t)
    fade_samples = min(int(sample_rate * 0.01), len(t) // 4)
    if fade_samples > 0:
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
    return (np.sin(2 * np.pi * frequency * t) * volume * envelope).astype(np.float32)


def _play_sound(audio: np.ndarray, sample_rate: int = 22050):
    """Play audio array through speakers."""
    if not _SD_AVAILABLE:
        return
    try:
        sd.play(audio, sample_rate)
        sd.wait()
    except Exception as e:
        logger.debug(f"Sound playback failed: {e}")


def play_wake_beep():
    """Short rising tone — wake word detected.
    
    200ms sweep from 440Hz to 880Hz. Feels responsive and snappy.
    """
    if not _SD_AVAILABLE:
        return
    
    sample_rate = 22050
    duration = 0.2
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Rising frequency sweep
    freq = np.linspace(440, 880, len(t))
    envelope = np.ones_like(t)
    fade = min(int(sample_rate * 0.01), len(t) // 4)
    if fade > 0:
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)
    
    audio = (np.sin(2 * np.pi * freq * t / sample_rate * np.arange(len(t))) * 0.25 * envelope).astype(np.float32)
    
    # Simpler approach: cumulative phase
    phase = np.cumsum(2 * np.pi * freq / sample_rate)
    audio = (np.sin(phase) * 0.25 * envelope).astype(np.float32)
    
    _play_sound(audio, sample_rate)


def play_success_beep():
    """Double short beep — command succeeded.
    
    Two quick 100ms tones at 660Hz and 880Hz.
    """
    if not _SD_AVAILABLE:
        return
    
    sample_rate = 22050
    tone1 = _generate_tone(660, 0.1, sample_rate, 0.2)
    gap = np.zeros(int(sample_rate * 0.05), dtype=np.float32)
    tone2 = _generate_tone(880, 0.1, sample_rate, 0.2)
    
    audio = np.concatenate([tone1, gap, tone2])
    _play_sound(audio, sample_rate)


def play_error_beep():
    """Low descending tone — command failed.
    
    300ms sweep from 440Hz to 220Hz. Distinct from success sound.
    """
    if not _SD_AVAILABLE:
        return
    
    sample_rate = 22050
    duration = 0.3
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    freq = np.linspace(440, 220, len(t))
    envelope = np.ones_like(t)
    fade = min(int(sample_rate * 0.015), len(t) // 4)
    if fade > 0:
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)
    
    phase = np.cumsum(2 * np.pi * freq / sample_rate)
    audio = (np.sin(phase) * 0.25 * envelope).astype(np.float32)
    
    _play_sound(audio, sample_rate)


def play_listening_beep():
    """Single soft beep — listening for command.
    
    Short 150ms tone at 523Hz (C5). Subtle notification that mic is active.
    """
    if not _SD_AVAILABLE:
        return
    
    audio = _generate_tone(523, 0.15, 22050, 0.15)
    _play_sound(audio, 22050)
