"""Voice CLI - Main voice interaction interface."""

import sys
import time
import threading
from datetime import datetime
from typing import Optional

from jarvis.voice.audio import AudioCapture, AudioConfig
from jarvis.voice.stt import SpeechToText, STTConfig
from jarvis.voice.tts import TextToSpeech, TTSConfig
from jarvis.voice.wake_word import WakeWordDetector, WakeWordConfig, PushToTalk
from jarvis.voice.sounds import play_wake_beep, play_success_beep, play_error_beep, play_listening_beep
from jarvis.utils.logger import get_logger
from jarvis.utils.config import config as app_config

logger = get_logger("voice.cli")


class VoiceInterface:
    def __init__(self):
        self.audio_config = AudioConfig(
            sample_rate=16000,
            chunk_size=1024,
            silence_threshold=500,
        )

        self.stt_config = STTConfig(
            model_size="base",
            language=None,
        )

        self.tts_config = TTSConfig(
            voice="en_US-lessac-medium",
            voice_dir="./voices",
        )

        # Build wake word keywords from config + defaults
        config_wake_word = app_config.wake_word.lower()
        default_keywords = ["hey gg", "gg", "hey jarvis", "jarvis", "hey jarvi", "jarvi" , "yo gg", "yo jarvis", "yo jarvi"]
        keywords = list(set(default_keywords + [config_wake_word]))

        self.wake_word_config = WakeWordConfig(
            engine="simple",
            keywords=keywords,
            sensitivity=0.5,
            porcupine_access_key=None,
        )

        self.audio_capture = AudioCapture(self.audio_config)
        self.stt = SpeechToText(self.stt_config)
        self.tts = TextToSpeech(self.tts_config)
        self.wake_word = WakeWordDetector(self.wake_word_config)
        self.push_to_talk = PushToTalk(self.audio_capture)

        self.brain = None
        self.running = False
        self.conversation_active = False

    def check_dependencies(self) -> dict:
        status = {
            "audio": self.audio_capture.is_available(),
            "stt": self.stt.is_available(),
            "tts": self.tts.is_available(),
        }

        if not status["audio"]:
            logger.warning("Audio capture not available. Install pyaudio.")

        if not status["stt"]:
            logger.warning("STT not available. Install faster-whisper.")

        if not status["tts"]:
            logger.warning("TTS not available. Install piper-tts.")

        return status

    def set_brain(self, brain):
        self.brain = brain

    def speak(self, text: str):
        if self.tts.is_available():
            self.tts.speak(text)
        else:
            print(f"JARVIS: {text}")

    def listen(self) -> str:
        if not self.stt.is_available():
            raise RuntimeError("STT not available")

        audio = self.audio_capture.record_until_silence(
            max_duration=30.0, silence_timeout=2.0
        )

        if len(audio) < 1600:
            return ""

        text = self.stt.transcribe(audio)
        return text.strip()

    def process_command(self, text: str) -> str:
        if not self.brain:
            return "Brain not connected. Cannot process command."

        response = self.brain.process(text)
        # Jarvis.process() returns a str directly
        return response if isinstance(response, str) else str(response)

    def conversation_loop(self):
        pass # Now handled in main thread loop safely

    def start(self):
        deps = self.check_dependencies()

        if not deps["audio"]:
            print("Error: Audio capture not available. Install pyaudio.")
            return False

        print("=" * 50)
        print("JARVIS Voice Interface")
        print("=" * 50)

        if deps["stt"]:
            print(f"STT: Whisper ({self.stt_config.model_size})")
        else:
            print("STT: Not available")

        if deps["tts"]:
            print(f"TTS: Piper ({self.tts_config.voice})")
        else:
            print("TTS: Not available")

        print("-" * 50)

        self.running = True
        self.wake_event = threading.Event()
        self.speak("Voice interface activated. Waiting for wake word.")
        self.wake_word.on_wake_word(self._on_wake_word)

        # Start background reminder and accountability checker
        threading.Thread(target=self._reminder_loop, daemon=True).start()

        try:
            while self.running:
                # 1. Start Wake Word mode reliably safely
                self.wake_event.clear()
                self.wake_word.start(self.audio_capture)

                # Wait for wake word trigger
                while self.running and not self.wake_event.is_set():
                    time.sleep(0.1)

                if not self.running:
                    break

                # 2. Wake word heard! STOP the ALSA mic stream fully
                self.wake_word.stop()
                
                # Instant audio feedback — much faster than TTS
                play_wake_beep()

                # Speak confirmation
                self.speak("Yes?")
                play_listening_beep()

                # 3. Open a NEW clean ALSA stt mic stream safely for exactly one command
                text = self.listen()
                
                if text:
                    print(f"You: {text}")

                    if any(word in text.lower() for word in ["goodbye", "exit", "quit", "stop", "nevermind"]):
                        self.speak("Goodbye!")
                        continue

                    response = self.process_command(text)
                    print(f"JARVIS: {response}")
                    self.speak(response)
                    play_success_beep()

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error(f"Voice loop error: {e}")
            self.stop()

        return True

    def _on_wake_word(self):
        logger.info("Wake word detected - activating conversation")
        self.wake_event.set()

    def _reminder_loop(self):
        """Background thread checking for scheduled reminders and announcements."""
        logger.info("Starting background reminder thread")
        last_check_minute = -1
        
        while self.running:
            try:
                now = datetime.now()
                # Run once per minute
                if now.minute != last_check_minute:
                    last_check_minute = now.minute
                    self._check_and_trigger_reminders(now)
            except Exception as e:
                logger.error(f"Error in reminder loop: {e}")
            time.sleep(10)

    def _check_and_trigger_reminders(self, now: datetime):
        """Check database for active habits with a reminder due now."""
        from jarvis.core.services import get_services
        
        try:
            services = get_services(self.brain.db if self.brain else None)
            habits = services.habits.get_habits(active_only=True)
            today_logs = {log.habit_id for log in services.habits.get_today_logs()}
            
            current_time_str = now.strftime("%H:%M") # e.g. "18:00"
            
            for habit in habits:
                if habit.reminder_time == current_time_str:
                    # If not completed today, play a voice reminder!
                    if habit.id not in today_logs:
                        message = f"Excuse me, GG. This is your scheduled reminder to do your habit: {habit.name}. Let's get to work!"
                        
                        # Use accountability style if possible
                        if services.accountability:
                            dream = services.accountability._get_dream_project()
                            message = f"GG, it is {current_time_str}. Time for your habit: {habit.name}. Remember, {dream} is built by showing up every single day. Let's do it!"
                        
                        logger.info(f"Triggering voice reminder for habit: {habit.name}")
                        # To avoid disrupting an active conversation, only speak if not in conversation
                        if not self.conversation_active:
                            # Speak in a separate thread so it doesn't block the loop
                            threading.Thread(target=self.speak, args=(message,), daemon=True).start()
                            
                            # Log it in the accountability log
                            if services.accountability:
                                services.accountability.log_accountability(
                                    trigger=f"Habit reminder: {habit.name}",
                                    message=message,
                                    action="Voice prompt spoken"
                                )
        except Exception as e:
            logger.error(f"Failed to check reminders: {e}")

    def stop(self):
        logger.info("Stopping voice interface...")
        self.running = False
        self.conversation_active = False
        self.wake_word.stop()
        self.audio_capture.close()
        print("Voice interface stopped.")

    def test_mode(self):
        deps = self.check_dependencies()

        print("Voice Interface Test Mode")
        print("-" * 40)

        if deps["audio"]:
            devices = self.audio_capture.list_devices()
            print(f"Found {len(devices)} audio input device(s):")
            for dev in devices:
                print(f"  - {dev['name']} (rate: {dev['sample_rate']})")
        else:
            print("No audio devices available")

        if deps["stt"]:
            print("\nSTT Test: Say something...")
            try:
                audio = self.audio_capture.record_until_silence(max_duration=5.0)
                if len(audio) > 0:
                    text = self.stt.transcribe(audio)
                    print(f"You said: {text}")
                else:
                    print("No audio captured")
            except Exception as e:
                print(f"STT test failed: {e}")

        if deps["tts"]:
            print("\nTTS Test: Speaking...")
            self.speak("This is a test of the text to speech system.")

        print("\nTest complete.")


def run_voice_interface(
    mode: str = "wake",
    test: bool = False,
    push_to_talk: bool = False,
    brain=None,
):
    voice = VoiceInterface()
    if brain:
        voice.set_brain(brain)

    if test:
        voice.test_mode()
        return

    if not voice.check_dependencies()["audio"]:
        print("Error: Audio not available")
        return

    if push_to_talk:
        run_push_to_talk(voice)
    elif mode == "wake":
        voice.start()
    else:
        run_continuous_listen(voice)


def run_push_to_talk(voice: VoiceInterface):
    print("Push-to-Talk Mode")
    print("Press Enter and speak, or Ctrl+C to exit")
    print("-" * 40)

    voice.speak("Push to talk mode. Press Enter and speak.")

    try:
        while True:
            input("\nPress Enter to speak...")

            audio = voice.push_to_talk.listen()

            if len(audio) < 1600:
                print("No speech detected")
                continue

            text = voice.stt.transcribe(audio)
            print(f"You said: {text}")

            if text:
                response = voice.process_command(text)
                print(f"JARVIS: {response}")
                voice.speak(response)

    except KeyboardInterrupt:
        print("\nExiting...")
        voice.audio_capture.close()


def run_continuous_listen(voice: VoiceInterface):
    print("Continuous Listen Mode")
    print("-" * 40)

    voice.speak("Continuous listening mode. Say 'exit' to quit.")

    while True:
        try:
            audio = voice.audio_capture.record_until_silence(
                max_duration=30.0, silence_timeout=2.0
            )

            if len(audio) > 1600:
                text = voice.stt.transcribe(audio)

                if text.lower().strip() in ["exit", "quit", "stop"]:
                    break

                if text:
                    print(f"You: {text}")
                    response = voice.process_command(text)
                    print(f"JARVIS: {response}")
                    voice.speak(response)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}")

    voice.audio_capture.close()
