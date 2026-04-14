"""Memory engine for context management."""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Optional
from datetime import timedelta

from jarvis.utils.logger import get_logger

logger = get_logger("core.memory")


@dataclass
class SessionMemory:
    """Short-term memory for current session."""

    recent_commands: list[dict] = field(default_factory=list)
    current_topic: Optional[str] = None
    pending_confirmation: Optional[dict] = None
    last_result: Any = None

    def add_command(self, command: str, intent: str, success: bool):
        """Add a command to history."""
        self.recent_commands.append(
            {
                "command": command,
                "intent": intent,
                "success": success,
                "timestamp": datetime.now(),
            }
        )
        if len(self.recent_commands) > 10:
            self.recent_commands.pop(0)

    def clear(self):
        """Clear session memory."""
        self.recent_commands.clear()
        self.current_topic = None
        self.pending_confirmation = None
        self.last_result = None


@dataclass
class UserPreferences:
    """User preferences and learned habits."""

    name: Optional[str] = None
    timezone: str = "UTC"
    default_energy: int = 5
    response_style: str = "normal"
    theme: str = "auto"
    voice_enabled: bool = False
    university_connected: bool = False


@dataclass
class DailyContext:
    """Daily context for scheduling."""

    date: date
    energy_level: Optional[int] = None
    mood: Optional[str] = None
    tasks_completed: int = 0
    notes: Optional[str] = None

    def is_morning(self) -> bool:
        hour = datetime.now().hour
        return 5 <= hour < 12

    def is_afternoon(self) -> bool:
        hour = datetime.now().hour
        return 12 <= hour < 17

    def is_evening(self) -> bool:
        hour = datetime.now().hour
        return 17 <= hour < 22

    def is_night(self) -> bool:
        hour = datetime.now().hour
        return 22 <= hour or hour < 5


class MemoryEngine:
    """Manages memory and context across sessions."""

    def __init__(self, db=None):
        self.session = SessionMemory()
        self.preferences = UserPreferences()
        self._daily_context: Optional[DailyContext] = None
        self.db = db

    def initialize(self):
        """Initialize memory from database."""
        if self.db:
            self._load_preferences()
            self._load_daily_context()

    def _load_preferences(self):
        """Load user preferences from database."""
        try:
            row = self.db.query_one("SELECT * FROM profile LIMIT 1")
            if row:
                self.preferences.name = row.get("name")
        except Exception as e:
            logger.debug(f"Could not load preferences: {e}")

    def _load_daily_context(self):
        """Load today's context from database."""
        try:
            today = date.today().isoformat()
            row = self.db.query_one("SELECT * FROM daily_logs WHERE date = ?", (today,))
            if row:
                self._daily_context = DailyContext(
                    date=date.fromisoformat(row["date"]),
                    energy_level=row.get("energy_level"),
                    productivity_score=row.get("productivity_score"),
                    notes=row.get("notes"),
                )
            else:
                self._daily_context = DailyContext(date=date.today())
        except Exception as e:
            logger.debug(f"Could not load daily context: {e}")
            self._daily_context = DailyContext(date=date.today())

    def get_daily_context(self) -> DailyContext:
        """Get today's context, creating if needed."""
        if not self._daily_context or self._daily_context.date != date.today():
            self._daily_context = DailyContext(date=date.today())
        return self._daily_context

    def update_energy(self, level: int):
        """Update today's energy level."""
        ctx = self.get_daily_context()
        ctx.energy_level = level

        if self.db:
            try:
                self.db.execute(
                    """
                    INSERT OR REPLACE INTO daily_logs (date, energy_level, productivity_score, notes)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        date.today().isoformat(),
                        level,
                        ctx.productivity_score,
                        ctx.notes,
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to save energy: {e}")

    def record_completed_task(self):
        """Record task completion."""
        ctx = self.get_daily_context()
        ctx.tasks_completed += 1

    def get_greeting(self) -> str:
        """Get appropriate greeting based on time."""
        ctx = self.get_daily_context()

        if ctx.is_morning():
            return "Good morning!"
        elif ctx.is_afternoon():
            return "Good afternoon!"
        elif ctx.is_evening():
            return "Good evening!"
        else:
            return "Hello!"

    def get_time_based_suggestion(self) -> Optional[str]:
        """Get suggestion based on time of day."""
        ctx = self.get_daily_context()

        if ctx.is_morning() and ctx.energy_level and ctx.energy_level >= 7:
            return "You're energized! Great time for deep work."
        elif ctx.is_afternoon() and ctx.energy_level and ctx.energy_level < 5:
            return "Energy is lower. Consider lighter tasks."
        elif ctx.is_evening():
            return "Wrapping up for the day?"

        return None

    def to_context(self) -> "Context":
        """Convert to brain Context."""
        from jarvis.core.brain import Context

        return Context(
            db=self.db,
            user_name=self.preferences.name,
        )
