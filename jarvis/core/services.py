"""Service registry for centralized, lazy-initialized service access.

Eliminates the pattern of creating `get_db() + ServiceX(get_db())`
in every CLI command. Services are created once and reused.
"""

from pathlib import Path
from typing import Optional

from jarvis.db.database import Database
from jarvis.utils.config import config
from jarvis.utils.logger import get_logger

logger = get_logger("core.services")


class ServiceRegistry:
    """Centralized service registry with lazy initialization.

    Usage:
        services = get_services()
        services.tasks.list(status=TaskStatus.PENDING)
        services.habits.get_habits()
    """

    def __init__(self, db: Optional[Database] = None):
        self._db = db
        self._cache = {}

    @property
    def db(self) -> Database:
        """Get or create the shared database instance."""
        if self._db is None:
            self._db = Database(config.db_path)
            self._db.initialize()
        return self._db

    def _get(self, name: str, factory):
        """Get a cached service instance, creating it if needed."""
        if name not in self._cache:
            self._cache[name] = factory(self.db)
        return self._cache[name]

    @property
    def tasks(self):
        from jarvis.skills.tasks import TaskService
        return self._get("tasks", TaskService)

    @property
    def notes(self):
        from jarvis.skills.notes import NoteService
        return self._get("notes", NoteService)

    @property
    def knowledge(self):
        from jarvis.skills.knowledge import KnowledgeService
        return self._get("knowledge", KnowledgeService)

    @property
    def habits(self):
        from jarvis.skills.habits import HabitService
        return self._get("habits", HabitService)

    @property
    def goals(self):
        from jarvis.skills.goals import GoalService
        return self._get("goals", GoalService)

    @property
    def profile(self):
        from jarvis.skills.profile import ProfileService
        return self._get("profile", ProfileService)

    @property
    def reviews(self):
        from jarvis.skills.reviews import ReviewService
        return self._get("reviews", ReviewService)

    @property
    def briefing(self):
        from jarvis.skills.briefing import BriefingService
        return self._get("briefing", BriefingService)

    @property
    def daily_tasks(self):
        from jarvis.skills.daily_tasks import DailyTaskService
        return self._get("daily_tasks", DailyTaskService)

    @property
    def accountability(self):
        """AccountabilityEngine requires multiple services — built from registry."""
        if "accountability" not in self._cache:
            from jarvis.skills.accountability import AccountabilityEngine
            self._cache["accountability"] = AccountabilityEngine(
                self.db, self.profile, self.goals, self.habits, self.reviews
            )
        return self._cache["accountability"]


# Module-level singleton — lazy, thread-safe for CLI
_registry: Optional[ServiceRegistry] = None


def get_services(db: Optional[Database] = None) -> ServiceRegistry:
    """Get the shared service registry (singleton).

    First call initializes the registry. Subsequent calls return the same instance.
    """
    global _registry
    if _registry is None:
        _registry = ServiceRegistry(db)
    return _registry
