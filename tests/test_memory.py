"""Tests for conversation memory and context resolution."""

import pytest
from jarvis.core.memory import MemoryEngine, SessionMemory, ConversationTurn


@pytest.fixture
def memory():
    return MemoryEngine()


@pytest.fixture
def session_with_tasks(memory):
    """Session with a prior task listing exchange."""
    session = memory.session

    session.add_turn("user", "what tasks do I have?")
    session.add_turn(
        "assistant",
        "You have 3 tasks",
        intent="list_tasks",
        response_data=[
            {"id": "abc", "title": "Study Python"},
            {"id": "def", "title": "Write essay"},
            {"id": "ghi", "title": "Fix bugs"},
        ],
    )
    return memory


class TestConversationTurn:
    """Test conversation turn storage."""

    def test_add_turn(self, memory):
        memory.session.add_turn("user", "hello")
        assert len(memory.session.conversation_history) == 1

    def test_turn_has_role(self, memory):
        memory.session.add_turn("user", "test")
        turn = memory.session.conversation_history[0]
        assert turn.role == "user"
        assert turn.text == "test"

    def test_turn_has_timestamp(self, memory):
        memory.session.add_turn("user", "test")
        turn = memory.session.conversation_history[0]
        assert turn.timestamp is not None

    def test_sliding_window(self, memory):
        """History should cap at 20 turns."""
        for i in range(25):
            memory.session.add_turn("user", f"message {i}")
        assert len(memory.session.conversation_history) <= 20


class TestReferenceResolution:
    """Test resolving ordinal and pronoun references."""

    def test_first_one(self, session_with_tasks):
        resolved = session_with_tasks.resolve_reference("mark the first one done")
        assert "Study Python" in resolved

    def test_second_one(self, session_with_tasks):
        resolved = session_with_tasks.resolve_reference("delete the second one")
        assert "Write essay" in resolved

    def test_last_one(self, session_with_tasks):
        resolved = session_with_tasks.resolve_reference("complete the last one")
        assert "Fix bugs" in resolved

    def test_no_reference(self, session_with_tasks):
        """Text without references should pass through unchanged."""
        result = session_with_tasks.resolve_reference("add task buy milk")
        assert result == "add task buy milk"

    def test_no_history(self, memory):
        """Should return original text when no history exists."""
        result = memory.resolve_reference("mark the first one done")
        assert "first one" in result  # No data to substitute


class TestMemoryEngine:
    """Test MemoryEngine initialization and state."""

    def test_has_session(self, memory):
        assert memory.session is not None
        assert isinstance(memory.session, SessionMemory)

    def test_has_preferences(self, memory):
        assert memory.preferences is not None
