"""Decision engine - routes intents to skill handlers."""

from dataclasses import dataclass
from typing import Optional, Callable, Any
from datetime import datetime

from jarvis.core.intent_parser import Intent, IntentType
from jarvis.utils.logger import get_logger

logger = get_logger("core.brain")


@dataclass
class Response:
    """Response from skill execution."""

    success: bool
    message: str
    data: Any = None
    should_speak: bool = True


class SkillHandler:
    """Handler for a specific skill."""

    def __init__(self, name: str, handler: Callable):
        self.name = name
        self.handler = handler

    def execute(self, intent: Intent, context: "Context") -> Response:
        """Execute the handler."""
        try:
            result = self.handler(intent, context)
            if isinstance(result, Response):
                return result
            return Response(success=True, message=str(result))
        except Exception as e:
            logger.error(f"Handler error: {e}", extra={"handler": self.name})
            return Response(success=False, message=f"Error: {str(e)}")


class DecisionEngine:
    """Routes intents to appropriate handlers."""

    def __init__(self):
        self._handlers: dict[IntentType, SkillHandler] = {}
        self._context: Optional["Context"] = None

    def register(
        self, intent_type: IntentType, handler: Callable, skill_name: str = ""
    ):
        """Register a handler for an intent type."""
        self._handlers[intent_type] = SkillHandler(
            skill_name or intent_type.value, handler
        )
        logger.debug(f"Registered handler for {intent_type.value}")

    def set_context(self, context: "Context"):
        """Set execution context."""
        self._context = context

    def process(self, intent: Intent) -> Response:
        """Process an intent and return response."""
        logger.info(f"Processing intent: {intent.intent.value} (confidence: {intent.confidence:.2f})")

        # Very low confidence — ask for clarification
        if intent.confidence < 0.4 and intent.intent == IntentType.UNKNOWN:
            return Response(
                success=False,
                message="I'm not sure what you mean. Could you rephrase? Say 'help' for available commands.",
            )

        handler = self._handlers.get(intent.intent)

        if not handler:
            logger.warning(f"No handler for intent: {intent.intent.value}")
            return Response(
                success=False,
                message=f"I don't know how to handle '{intent.intent.value}'",
            )

        response = handler.execute(intent, self._context)

        # Add confidence note for fuzzy matches
        if 0.4 <= intent.confidence < 0.8 and response.success:
            response.message = f"(I think you meant: {intent.intent.value})\n{response.message}"

        return response


class Context:
    """Execution context passed to handlers."""

    def __init__(self, db=None, user_name: str = None):
        self.db = db
        self.user_name = user_name
        self.session_data: dict = {}
        self.timestamp = datetime.now()

    def get(self, key: str, default: Any = None) -> Any:
        """Get session data."""
        return self.session_data.get(key, default)

    def set(self, key: str, value: Any):
        """Set session data."""
        self.session_data[key] = value

    def clear(self):
        """Clear session data."""
        self.session_data.clear()
