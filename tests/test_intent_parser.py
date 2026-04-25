"""Tests for the intent parser."""

import pytest
from jarvis.core.intent_parser import IntentParser, IntentType, Intent


@pytest.fixture
def parser():
    return IntentParser()


class TestRegexParsing:
    """Test exact regex pattern matching (high confidence)."""

    def test_add_task(self, parser):
        result = parser.parse("add task buy groceries")
        assert result.intent == IntentType.ADD_TASK
        assert result.confidence == 0.9

    def test_add_task_natural(self, parser):
        result = parser.parse("i have to study math")
        assert result.intent == IntentType.ADD_TASK

    def test_add_task_should(self, parser):
        result = parser.parse("i should call mom")
        assert result.intent == IntentType.ADD_TASK

    def test_list_tasks(self, parser):
        result = parser.parse("show my tasks")
        assert result.intent == IntentType.LIST_TASKS

    def test_list_tasks_question(self, parser):
        result = parser.parse("what tasks do I have")
        assert result.intent == IntentType.LIST_TASKS

    def test_list_tasks_focus(self, parser):
        result = parser.parse("what should I focus on")
        assert result.intent == IntentType.LIST_TASKS

    def test_complete_task(self, parser):
        result = parser.parse("done study python")
        assert result.intent == IntentType.COMPLETE_TASK

    def test_complete_task_mark(self, parser):
        result = parser.parse("mark study python done")
        assert result.intent == IntentType.COMPLETE_TASK

    def test_add_note(self, parser):
        result = parser.parse("note meeting with team at 3pm")
        assert result.intent == IntentType.ADD_NOTE

    def test_search_notes(self, parser):
        result = parser.parse("search notes python")
        assert result.intent == IntentType.SEARCH_NOTES

    def test_briefing(self, parser):
        result = parser.parse("briefing")
        assert result.intent == IntentType.DAILY_BRIEFING

    def test_briefing_natural(self, parser):
        result = parser.parse("catch me up")
        assert result.intent == IntentType.DAILY_BRIEFING

    def test_briefing_morning(self, parser):
        result = parser.parse("good morning")
        assert result.intent == IntentType.DAILY_BRIEFING

    def test_status(self, parser):
        result = parser.parse("status")
        assert result.intent == IntentType.SHOW_STATUS

    def test_help(self, parser):
        result = parser.parse("help")
        assert result.intent == IntentType.HELP

    def test_log_habit(self, parser):
        result = parser.parse("log exercise")
        assert result.intent == IntentType.LOG_HABIT

    def test_log_habit_did(self, parser):
        result = parser.parse("did my meditation")
        assert result.intent == IntentType.LOG_HABIT

    def test_list_habits(self, parser):
        result = parser.parse("habits")
        assert result.intent == IntentType.LIST_HABITS

    def test_list_habits_show(self, parser):
        result = parser.parse("show my habits")
        assert result.intent == IntentType.LIST_HABITS

    def test_goal_status(self, parser):
        result = parser.parse("goals")
        assert result.intent == IntentType.GOAL_STATUS

    def test_goal_status_show(self, parser):
        result = parser.parse("show goals")
        assert result.intent == IntentType.GOAL_STATUS

    def test_set_energy(self, parser):
        result = parser.parse("energy 8")
        assert result.intent == IntentType.SET_ENERGY

    def test_set_energy_word(self, parser):
        result = parser.parse("energy high")
        assert result.intent == IntentType.SET_ENERGY


class TestFuzzyMatching:
    """Test fuzzy keyword fallback (lower confidence)."""

    def test_fuzzy_triggers_on_no_regex_match(self, parser):
        """Test that _fuzzy_match returns a result for keyword-heavy input."""
        # Use multiple keywords from a single intent's keyword set
        result = parser._fuzzy_match("add create new task todo")
        assert result is not None
        intent_type, confidence = result
        assert confidence < 0.9

    def test_fuzzy_returns_none_for_gibberish(self, parser):
        """Pure gibberish should not trigger fuzzy matching."""
        result = parser._fuzzy_match("xyzzy plugh qwerty")
        assert result is None

    def test_fuzzy_track_meditation(self, parser):
        result = parser.parse("track my meditation")
        assert result.intent == IntentType.LOG_HABIT

    def test_unknown_for_gibberish(self, parser):
        result = parser.parse("asdfghjkl")
        assert result.intent == IntentType.UNKNOWN
        assert result.confidence < 0.4

    def test_unknown_for_empty(self, parser):
        result = parser.parse("")
        assert result.intent == IntentType.UNKNOWN


class TestIntentProperties:
    """Test Intent dataclass properties."""

    def test_entities_extracted(self, parser):
        result = parser.parse("add task buy milk")
        assert "content" in result.entities or "title" in result.entities

    def test_source_propagated(self, parser):
        result = parser.parse("help", source="voice")
        assert result.source == "voice"

    def test_raw_text_preserved(self, parser):
        result = parser.parse("  ADD TASK Test  ")
        assert result.raw_text == "add task test"


class TestNoConflicts:
    """Test that similar patterns don't conflict."""

    def test_show_habits_not_tasks(self, parser):
        """'show my habits' must match LIST_HABITS not LIST_TASKS."""
        result = parser.parse("show my habits")
        assert result.intent == IntentType.LIST_HABITS

    def test_show_tasks_still_works(self, parser):
        result = parser.parse("show my tasks")
        assert result.intent == IntentType.LIST_TASKS

    def test_log_not_list(self, parser):
        """'log exercise' must match LOG_HABIT not LIST_HABITS."""
        result = parser.parse("log exercise")
        assert result.intent == IntentType.LOG_HABIT
