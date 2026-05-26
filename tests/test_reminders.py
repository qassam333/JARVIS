"""Tests for the silent reminder system in VoiceInterface."""

import pytest
import time
from datetime import datetime
from unittest.mock import patch, MagicMock

import jarvis.core.services
from jarvis.db.database import Database
from jarvis.core.services import ServiceRegistry, get_services
from jarvis.voice.voice_cli import VoiceInterface


@pytest.fixture
def clean_services(tmp_path):
    """Provide a fresh registry and database for the test."""
    # Reset singleton registry
    jarvis.core.services._registry = None
    
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.initialize()
    
    # Force initialize the singleton with our test db
    registry = get_services(db)
    return registry


@patch('jarvis.voice.voice_cli.AudioCapture')
@patch('jarvis.voice.voice_cli.SpeechToText')
@patch('jarvis.voice.voice_cli.TextToSpeech')
@patch('jarvis.voice.voice_cli.WakeWordDetector')
@patch('jarvis.voice.voice_cli.PushToTalk')
def test_reminder_fires_and_logs(mock_ptt, mock_wake, mock_tts, mock_stt, mock_audio, clean_services):
    db = clean_services.db
    
    # 1. Create a habit scheduled for a specific time
    reminder_time = "14:30"
    habit_id = clean_services.habits.create_habit(
        name="Go to Gym",
        reminder_time=reminder_time
    )
    
    # 2. Mock VoiceInterface
    interface = VoiceInterface()
    
    # Set brain mock
    brain_mock = MagicMock()
    brain_mock.db = db
    interface.set_brain(brain_mock)
    
    # Mock speak to capture the spoken message
    spoken_messages = []
    def mock_speak(message):
        spoken_messages.append(message)
    interface.speak = mock_speak
    
    # 3. Trigger reminder check at matching time (14:30)
    test_datetime = datetime(2026, 5, 26, 14, 30, 0)
    interface._check_and_trigger_reminders(test_datetime)
    
    # Since speak runs in a thread:
    # Let's wait up to 1 second for the thread to run mock_speak
    start_time = time.time()
    while not spoken_messages and time.time() - start_time < 1.0:
        time.sleep(0.05)
        
    # Check that speak was called with Gym reminder message
    assert len(spoken_messages) == 1
    assert "Go to Gym" in spoken_messages[0]
    
    # 4. Check that it was logged in the accountability logs
    logs = db.query("SELECT * FROM accountability_log")
    assert len(logs) == 1
    assert "Habit reminder: Go to Gym" in logs[0]["trigger"]
    assert "Voice prompt spoken" in logs[0]["action_taken"]
