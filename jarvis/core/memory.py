"""Memory engine for context management."""

import re
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from difflib import SequenceMatcher
from typing import Any, Optional

from jarvis.utils.logger import get_logger

logger = get_logger("core.memory")


@dataclass
class ConversationTurn:
    """A single exchange in a conversation."""

    role: str  # 'user' or 'assistant'
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    intent: Optional[str] = None
    entities: dict = field(default_factory=dict)
    response_data: Any = None  # e.g. list of tasks returned


@dataclass
class SessionMemory:
    """Short-term memory for current session."""

    recent_commands: list[dict] = field(default_factory=list)
    conversation_history: list[ConversationTurn] = field(default_factory=list)
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

    def add_turn(self, role: str, text: str, intent: str = None,
                 entities: dict = None, response_data: Any = None):
        """Add a conversation turn."""
        turn = ConversationTurn(
            role=role,
            text=text,
            intent=intent,
            entities=entities or {},
            response_data=response_data,
        )
        self.conversation_history.append(turn)
        # Keep last 20 turns
        if len(self.conversation_history) > 20:
            self.conversation_history.pop(0)

    def get_last_assistant_turn(self) -> Optional[ConversationTurn]:
        """Get the most recent assistant turn."""
        for turn in reversed(self.conversation_history):
            if turn.role == "assistant":
                return turn
        return None

    def get_last_user_turn(self) -> Optional[ConversationTurn]:
        """Get the most recent user turn."""
        for turn in reversed(self.conversation_history):
            if turn.role == "user":
                return turn
        return None

    def clear(self):
        """Clear session memory."""
        self.recent_commands.clear()
        self.conversation_history.clear()
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
    productivity_score: Optional[int] = None
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

    def resolve_reference(self, text: str) -> str:
        """Resolve pronoun/ordinal references from conversation context.

        Examples:
            'mark the first one done' -> 'mark <task_title> done'
            'tell me more about it' -> 'tell me more about <last_entity>'
        """
        text_lower = text.lower().strip()

        # Ordinal references: "the first one", "the second one", "number 2"
        ordinal_map = {
            "first": 0, "1st": 0, "number 1": 0, "the first one": 0,
            "second": 1, "2nd": 1, "number 2": 1, "the second one": 1,
            "third": 2, "3rd": 2, "number 3": 2, "the third one": 2,
            "fourth": 3, "4th": 3, "number 4": 3,
            "fifth": 4, "5th": 4, "number 5": 4,
            "last": -1, "the last one": -1,
        }

        last_turn = self.session.get_last_assistant_turn()
        if not last_turn or not last_turn.response_data:
            return text

        response_items = last_turn.response_data
        if not isinstance(response_items, list) or not response_items:
            return text

        # Check for ordinal references
        for pattern, index in ordinal_map.items():
            if pattern in text_lower:
                try:
                    item = response_items[index]
                    item_id = item.get("id", "") if isinstance(item, dict) else getattr(item, "id", "")
                    item_title = item.get("title", "") if isinstance(item, dict) else getattr(item, "title", "")

                    if item_id:
                        # Replace the ordinal reference with the actual identifier
                        result = re.sub(
                            r'(?:the\s+)?(?:first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th|last)(?:\s+one)?|number\s+\d',
                            item_title or item_id,
                            text_lower, count=1
                        )
                        logger.debug(f"Resolved reference: '{text}' -> '{result}'")
                        return result
                except (IndexError, AttributeError):
                    pass

        # Pronoun references: "it", "that", "this"
        if re.search(r'\b(it|that|this)\b', text_lower):
            # Use the first item from the last result
            if response_items:
                item = response_items[0]
                item_title = item.get("title", "") if isinstance(item, dict) else getattr(item, "title", "")
                if item_title:
                    result = re.sub(r'\b(it|that|this)\b', item_title, text_lower, count=1)
                    logger.debug(f"Resolved pronoun: '{text}' -> '{result}'")
                    return result

        return text

    def to_context(self) -> "Context":
        """Convert to brain Context."""
        from jarvis.core.brain import Context

        return Context(
            db=self.db,
            user_name=self.preferences.name,
        )
