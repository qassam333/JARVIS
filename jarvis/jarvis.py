"""JARVIS - The main assistant class."""

from pathlib import Path

from jarvis.core.intent_parser import IntentParser, Intent
from jarvis.core.brain import DecisionEngine, Context
from jarvis.core.memory import MemoryEngine
from jarvis.core import handlers
from jarvis.db.database import Database
from jarvis.utils.logger import setup_logger, get_logger

logger = get_logger("jarvis")


class Jarvis:
    """Main JARVIS assistant."""

    def __init__(self, db_path: str = None):
        self.logger = logger
        self.parser = IntentParser()
        self.brain = DecisionEngine()
        self.memory = MemoryEngine()
        self.db = Database(Path(db_path)) if db_path else Database()

        self._setup_handlers()
        self._setup_context()

    def _setup_handlers(self):
        """Register all intent handlers."""
        from jarvis.core.intent_parser import IntentType

        self.brain.register(IntentType.ADD_TASK, handlers.handle_add_task, "tasks")
        self.brain.register(IntentType.LIST_TASKS, handlers.handle_list_tasks, "tasks")
        self.brain.register(
            IntentType.COMPLETE_TASK, handlers.handle_complete_task, "tasks"
        )
        self.brain.register(IntentType.ADD_NOTE, handlers.handle_add_note, "notes")
        self.brain.register(
            IntentType.SEARCH_NOTES, handlers.handle_search_notes, "notes"
        )
        self.brain.register(
            IntentType.ADD_KNOWLEDGE, handlers.handle_add_knowledge, "knowledge"
        )
        self.brain.register(
            IntentType.SEARCH_KNOWLEDGE, handlers.handle_search_knowledge, "knowledge"
        )
        self.brain.register(
            IntentType.SHOW_STATUS, handlers.handle_show_status, "status"
        )
        self.brain.register(
            IntentType.SCHEDULE_TODAY, handlers.handle_schedule, "schedule"
        )
        self.brain.register(
            IntentType.DAILY_BRIEFING, handlers.handle_briefing, "briefing"
        )
        self.brain.register(
            IntentType.UNIVERSITY_SYNC, handlers.handle_university_sync, "university"
        )
        self.brain.register(IntentType.HELP, handlers.handle_help, "help")
        self.brain.register(IntentType.UNKNOWN, handlers.handle_unknown, "unknown")

    def _setup_context(self):
        """Setup execution context."""
        context = Context(
            db=self.db,
            user_name=self.memory.preferences.name,
        )
        self.brain.set_context(context)
        self.memory.db = self.db
        self.memory.initialize()

    def process(self, text: str, source: str = "text") -> str:
        """
        Process user input and return response.

        Args:
            text: User input text
            source: Source of input (text, voice, etc.)

        Returns:
            Response message string
        """
        self.logger.info(f"Processing: {text}")

        intent = self.parser.parse(text, source)

        self.memory.session.add_command(text, intent.intent.value, True)

        response = self.brain.process(intent)

        self.memory.session.last_result = response

        return response.message

    def greet(self) -> str:
        """Get greeting message."""
        return self.memory.get_greeting()

    def initialize(self):
        """Initialize database."""
        self.db.initialize()
        self._setup_context()
