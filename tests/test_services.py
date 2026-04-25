"""Tests for the service registry."""

import pytest
from pathlib import Path
from jarvis.core.services import ServiceRegistry, get_services


@pytest.fixture
def registry(tmp_path):
    """Create a registry with a temp database."""
    from jarvis.db.database import Database

    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.initialize()
    return ServiceRegistry(db)


class TestServiceRegistry:
    """Test centralized service instantiation and caching."""

    def test_db_property(self, registry):
        assert registry.db is not None

    def test_tasks_service(self, registry):
        from jarvis.skills.tasks import TaskService
        assert isinstance(registry.tasks, TaskService)

    def test_habits_service(self, registry):
        from jarvis.skills.habits import HabitService
        assert isinstance(registry.habits, HabitService)

    def test_goals_service(self, registry):
        from jarvis.skills.goals import GoalService
        assert isinstance(registry.goals, GoalService)

    def test_notes_service(self, registry):
        from jarvis.skills.notes import NoteService
        assert isinstance(registry.notes, NoteService)

    def test_knowledge_service(self, registry):
        from jarvis.skills.knowledge import KnowledgeService
        assert isinstance(registry.knowledge, KnowledgeService)

    def test_profile_service(self, registry):
        from jarvis.skills.profile import ProfileService
        assert isinstance(registry.profile, ProfileService)

    def test_reviews_service(self, registry):
        from jarvis.skills.reviews import ReviewService
        assert isinstance(registry.reviews, ReviewService)

    def test_briefing_service(self, registry):
        from jarvis.skills.briefing import BriefingService
        assert isinstance(registry.briefing, BriefingService)

    def test_daily_tasks_service(self, registry):
        from jarvis.skills.daily_tasks import DailyTaskService
        assert isinstance(registry.daily_tasks, DailyTaskService)

    def test_accountability_engine(self, registry):
        from jarvis.skills.accountability import AccountabilityEngine
        assert isinstance(registry.accountability, AccountabilityEngine)


class TestServiceCaching:
    """Test that services are cached (same instance on repeated access)."""

    def test_tasks_cached(self, registry):
        a = registry.tasks
        b = registry.tasks
        assert a is b

    def test_habits_cached(self, registry):
        a = registry.habits
        b = registry.habits
        assert a is b

    def test_goals_cached(self, registry):
        a = registry.goals
        b = registry.goals
        assert a is b

    def test_accountability_cached(self, registry):
        a = registry.accountability
        b = registry.accountability
        assert a is b
