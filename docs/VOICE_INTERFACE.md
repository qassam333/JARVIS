# Voice Interface Documentation

> **Purpose**: Enable voice interaction with JARVIS using local, privacy-preserving technologies.

---

## Overview

The voice interface provides hands-free interaction:

```
┌─────────────────────────────────────────────────────────────┐
│                    VOICE PIPELINE                            │
│                                                              │
│  ┌──────────────┐                                           │
│  │  Microphone  │ (continuous audio stream)                 │
│  └──────┬───────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              WAKE WORD DETECTION                       │  │
│  │   Listens for "Hey JARVIS" continuously               │  │
│  │   Uses minimal CPU when idle                           │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │ Wake detected                      │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              SPEECH-TO-TEXT (STT)                      │  │
│  │   • Whisper.cpp (local, no cloud)                    │  │
│  │   • Converts spoken words to text                    │  │
│  │   • Multiple language support                        │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                     │
│                         ▼ Text input                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              JARVIS CORE (Brain)                       │  │
│  │   • Intent parsing                                    │  │
│  │   • Decision engine                                   │  │
│  │   • Execute action                                    │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                     │
│                         ▼ Text response                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              TEXT-TO-SPEECH (TTS)                      │  │
│  │   • Piper (local, no cloud)                          │  │
│  │   • Converts text response to audio                  │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                     │
│                         ▼ Audio output                        │
│  ┌──────────────┐                                           │
│  │   Speaker    │ (JARVIS speaks back)                     │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
jarvis/voice/
├── __init__.py        # Module exports
├── wake_word.py       # "Hey JARVIS" detection
├── stt.py             # Speech-to-text (Whisper)
├── tts.py             # Text-to-speech (Piper)
├── audio.py           # Audio utilities
└── voice_cli.py       # Voice interaction loop
```

---

## Component 1: Wake Word Detection

### Purpose

Detect when user says "Hey JARVIS" to activate voice mode.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                 WAKE WORD DETECTION FLOW                     │
│                                                              │
│  AUDIO STREAM:  [chunk] [chunk] [chunk] [chunk] ...         │
│                      │        │        │        │            │
│                      ▼        ▼        ▼        ▼            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              VOICE ACTIVITY DETECTION (VAD)           │   │
│  │   • Is this chunk speech?                            │   │
│  │   • Silences are skipped                            │   │
│  │   • Only process speech audio                        │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              KEYWORD DETECTION                        │   │
│  │   • Match audio against "hey jarvis"               │   │
│  │   • Uses Porcupine/snowboy/porcupine               │   │
│  │   • Runs continuously (low CPU)                    │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│            ┌────────────┴────────────┐                       │
│            │                         │                       │
│            ▼                         ▼                       │
│  ┌─────────────────┐       ┌─────────────────┐              │
│  │   NO MATCH      │       │   MATCH!        │              │
│  │   Continue      │       │   Trigger STT   │              │
│  │   listening     │       │   recording     │              │
│  └─────────────────┘       └─────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Options

| Library | Pros | Cons | License |
|---------|------|------|--------|
| **Porcupine** | Accurate, fast, small | Commercial use needs license | Proprietary |
| **Snowboy** | Open source | Deprecated, no updates | BSD |
| **Picovoice** | Free for personal | Rate limits | Proprietary |
| **Webrtc VAD** | Open source | Basic detection | BSD |
| **Custom** | Full control | More work | Your choice |

### Porcupine Implementation (Recommended)

```python
import pvporcupine

class WakeWordDetector:
    """Wake word detection using Porcupine"""
    
    def __init__(self, keywords: list[str] = ["hey jarvis"]):
        # Access key from Picovoice console (free)
        self.porcupine = pvporcupine.create(
            access_key="YOUR_ACCESS_KEY",
            keywords=keywords,
            sensitivities=[0.5] * len(keywords)
        )
        self.running = False
    
    def start(self, audio_stream):
        """Start listening for wake word"""
        self.running = True
        
        while self.running:
            # Read audio chunk
            pcm = audio_stream.read(self.porcupine.frame_length)
            
            # Process with Porcupine
            keyword_index = self.porcupine.process(pcm)
            
            if keyword_index >= 0:
                # Wake word detected!
                self.on_wake_word_detected()
    
    def on_wake_word_detected(self):
        """Override to handle detection"""
        pass
```

### Privacy Modes

| Mode | Behavior | Privacy Level |
|------|----------|---------------|
| **Always Listening** | Mic on, wake word detection active | Medium (audio processed locally only) |
| **Push-to-Talk** | Button/key to activate | High (no continuous listening) |
| **Manual Voice** | Run `jarvis voice` command | Highest (full control) |

---

## Component 2: Speech-to-Text (STT)

### Technology: Whisper.cpp

**Why Whisper.cpp?**

| Feature | Benefit |
|---------|---------|
| 100% Local | No data sent to cloud |
| Multiple Languages | Supports Arabic, English, etc. |
| Various Model Sizes | Balance speed/accuracy |
| CPU Inference | No GPU required |
| Open Source | Auditable, modifiable |

### Model Sizes

| Model | Size | RAM Usage | Speed | Best For |
|-------|------|-----------|-------|----------|
| tiny | 39 MB | ~100 MB | ~10x realtime | Testing |
| base | 74 MB | ~200 MB | ~5x realtime | Recommended (your 16GB) |
| small | 244 MB | ~500 MB | ~2x realtime | Better accuracy |
| medium | 769 MB | ~1.5 GB | ~1x realtime | Best accuracy |

### STT Implementation

```python
import whisper
import numpy as np

class SpeechToText:
    """Local speech-to-text using Whisper"""
    
    def __init__(self, model_size: str = "base"):
        # Load model once at startup
        self.model = whisper.load_model(model_size)
        print(f"Whisper {model_size} loaded")
    
    def transcribe(self, audio: np.ndarray) -> str:
        """
        Convert audio to text
        
        Args:
            audio: numpy array of audio samples (16kHz, mono)
        
        Returns:
            Recognized text
        """
        # Transcribe with Whisper
        result = self.model.transcribe(
            audio,
            language="auto",  # Auto-detect, or specify "en", "ar", etc.
            fp16=False  # Use CPU
        )
        
        return result["text"].strip()
    
    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe audio file"""
        result = self.model.transcribe(audio_path, fp16=False)
        return result["text"].strip()
```

### Recording After Wake Word

```python
import pyaudio
import wave

class VoiceRecorder:
    """Record audio after wake word detected"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.audio = pyaudio.PyAudio()
    
    def record_until_silence(self, timeout: float = 5.0) -> np.ndarray:
        """Record until silence detected or timeout"""
        
        frames = []
        silence_threshold = 500  # Adjust based on testing
        max_silence_frames = 30  # ~0.5 seconds of silence
        
        silent_frames = 0
        recording = True
        
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024
        )
        
        while recording:
            data = stream.read(1024)
            frames.append(data)
            
            # Check for silence
            audio_data = np.frombuffer(data, dtype=np.int16)
            if np.abs(audio_data).mean() < silence_threshold:
                silent_frames += 1
                if silent_frames > max_silence_frames:
                    recording = False
            else:
                silent_frames = 0
        
        stream.stop_stream()
        stream.close()
        
        # Convert to numpy array
        audio = np.frombuffer(b''.join(frames), dtype=np.int16)
        audio = audio.astype(np.float32) / 32768.0
        
        return audio
```

---

## Component 3: Text-to-Speech (TTS)

### Technology: Piper

**Why Piper?**

| Feature | Benefit |
|---------|---------|
| 100% Local | Privacy preserved |
| Fast Inference | Real-time capable |
| Neural Voices | Natural sounding |
| Low Resource | Runs on CPU |
| Custom Voices | Train on your voice (future) |

### Installation

```bash
# Download Piper
wget https://github.com/rhasspy/piper/releases/latest/download/piper_linux_amd64.tar.gz
tar -xzf piper_linux_amd64.tar.gz

# Download English voice model
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

### TTS Implementation

```python
import subprocess
import tempfile
import os
from pathlib import Path

class TextToSpeech:
    """Local TTS using Piper"""
    
    def __init__(self, model_path: str, config_path: str):
        self.model_path = model_path
        self.config_path = config_path
    
    def speak(self, text: str):
        """Speak text aloud"""
        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name
        
        try:
            # Run Piper
            subprocess.run([
                "./piper",
                "--model", self.model_path,
                "--config", self.config_path,
                "--output_file", output_path
            ], input=text.encode(), check=True)
            
            # Play audio
            self._play_audio(output_path)
        
        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def _play_audio(self, audio_path: str):
        """Play WAV file"""
        # Using aplay, paplay, or pygame
        subprocess.run(["aplay", audio_path], check=True)
    
    def text_to_file(self, text: str, output_path: str):
        """Save speech to file instead of playing"""
        subprocess.run([
            "./piper",
            "--model", self.model_path,
            "--config", self.config_path,
            "--output_file", output_path
        ], input=text.encode(), check=True)
```

---

## Voice CLI Integration

### Main Voice Loop

```python
import threading
from jarvis.voice.wake_word import WakeWordDetector
from jarvis.voice.stt import SpeechToText
from jarvis.voice.tts import TextToSpeech

class VoiceInterface:
    """Complete voice interaction system"""
    
    def __init__(self):
        # Initialize components
        self.wake_word = WakeWordDetector(keywords=["hey jarvis"])
        self.stt = SpeechToText(model_size="base")
        self.tts = TextToSpeech(
            model_path="./voices/en_US-lessac-medium.onnx",
            config_path="./voices/en_US-lessac-medium.onnx.json"
        )
        
        # Audio capture
        self.audio = AudioCapture()
        
        # JARVIS core
        self.brain = Brain()
        
        # State
        self.active = False
    
    def start(self):
        """Start voice interface"""
        print("🎙️ JARVIS Voice Interface started")
        print("Say 'Hey JARVIS' to activate...")
        
        # Start wake word detection in background
        wake_thread = threading.Thread(target=self._listen_for_wake)
        wake_thread.daemon = True
        wake_thread.start()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def _listen_for_wake(self):
        """Background thread: listen for wake word"""
        while True:
            if self.wake_word.detect(self.audio):
                self._handle_activation()
    
    def _handle_activation(self):
        """Handle wake word activation"""
        print("🎤 Activated!")
        
        # Give audio cue
        self.tts.speak("Yes?")
        
        # Record command
        audio = self.audio.record_until_silence()
        
        # Transcribe
        command = self.stt.transcribe(audio)
        print(f"You said: {command}")
        
        # Process with JARVIS brain
        response = self.brain.process(command)
        
        # Speak response
        self.tts.speak(response.message)
    
    def stop(self):
        """Stop voice interface"""
        self.active = False
        print("Voice interface stopped")
```

### CLI Command

```bash
# Start voice mode
jarvis voice

# Or with specific wake word
jarvis voice --wake-word "hey assistant"

# Test mode (no wake word, always listening)
jarvis voice --test

# Push-to-talk mode
jarvis voice --ptt
```

---

## Voice Commands

### Supported Commands

| Category | Example | Action |
|----------|---------|--------|
| **Tasks** | "Add task study math" | Create task |
| **Tasks** | "What do I have today?" | List tasks |
| **Tasks** | "Complete task one" | Mark done |
| **Notes** | "Take a note about meeting" | Create note |
| **Notes** | "Show my notes about project" | Search notes |
| **Knowledge** | "Remember that Python uses indentation" | Add fact |
| **Schedule** | "What's my schedule today?" | Show schedule |
| **University** | "Sync my university" | Trigger sync |
| **General** | "Good morning" | Morning briefing |
| **Help** | "What can you do?" | Show capabilities |

### Example Conversations

```
User: "Hey JARVIS, remind me to study for my math exam"
JARVIS: "I've added 'Study for math exam' to your tasks. When is it due?"
User: "Next Friday"
JARVIS: "Due date set for next Friday. Anything else?"

---

User: "Hey JARVIS, what's on my schedule today?"
JARVIS: "Today you have:
- Study math (morning, high energy)
- University lecture at 2pm
- Gym session (afternoon)
You have 3 tasks pending. Would you like me to generate a schedule?"

---

User: "Hey JARVIS, good morning"
JARVIS: "Good morning! Today is Monday, January 15th.
Energy level: Good (7/10)
Tasks due: 2
University: 1 new assignment from Computer Science
Weather: Sunny, 22°C
Would you like your daily briefing?"
```

---

## Audio Utilities

### Audio Capture

```python
import pyaudio
import numpy as np

class AudioCapture:
    """Capture audio from microphone"""
    
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()
    
    def get_stream(self):
        """Get audio stream"""
        return self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
    
    def read_chunk(self, stream) -> np.ndarray:
        """Read one chunk of audio"""
        data = stream.read(self.chunk_size)
        audio = np.frombuffer(data, dtype=np.int16)
        return audio.astype(np.float32) / 32768.0
    
    def close(self):
        """Clean up audio resources"""
        self.audio.terminate()
```

### Audio Processing

```python
def preprocess_audio(audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
    """Preprocess audio for Whisper"""
    
    # Normalize
    audio = audio / np.max(np.abs(audio))
    
    # Resample if needed
    # (Whisper expects 16kHz)
    
    # Trim silence
    # (Remove leading/trailing silence)
    
    return audio
```

---

## Configuration

### Voice Config (config.yaml)

```yaml
voice:
  enabled: true
  
  wake_word:
    engine: "porcupine"  # porcupine, snowboy, webrtc
    keywords:
      - "hey jarvis"
    sensitivity: 0.5
    audio_gain: 1.0
  
  stt:
    engine: "whisper"
    model: "base"  # tiny, base, small, medium
    language: "auto"  # auto, en, ar, etc.
  
  tts:
    engine: "piper"
    voice: "en_US-lessac-medium"
    speaking_rate: 1.0
    volume: 1.0
  
  audio:
    sample_rate: 16000
    chunk_size: 1024
    silence_threshold: 500
```

---

## Troubleshooting

### Wake Word Not Detecting

| Issue | Solution |
|-------|----------|
| Too quiet | Move closer to mic, increase gain |
| Background noise | Use noise-canceling mic |
| Wrong language | Set correct language in config |
| Sensitivity too low | Increase sensitivity (0.7) |

### STT Accuracy Issues

| Issue | Solution |
|-------|----------|
| Wrong language | Set explicit language |
| Accented speech | Use "small" or "medium" model |
| Background noise | Record in quieter environment |
| Too fast | Speak more slowly |

### TTS Quality Issues

| Issue | Solution |
|-------|----------|
| Robotic voice | Try different voice model |
| Too slow | Increase speaking_rate |
| Wrong language | Download language-specific voice |

---

## Privacy & Security

| Concern | Solution |
|---------|----------|
| Audio never leaves device | Whisper + Piper run locally |
| No cloud transcription | All STT done on-device |
| Wake word processed locally | Porcupine runs on-device |
| No audio storage | Audio discarded after processing |
| Microphone access | Only when voice mode active |

---

<div align="center">

**Your voice stays on your device.**

</div>
