"""Intent parser for natural language understanding."""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Any
from enum import Enum

from jarvis.utils.logger import get_logger

logger = get_logger("core.intent_parser")


class IntentType(str, Enum):
    ADD_TASK = "add_task"
    LIST_TASKS = "list_tasks"
    COMPLETE_TASK = "complete_task"
    DELETE_TASK = "delete_task"
    ADD_NOTE = "add_note"
    SEARCH_NOTES = "search_notes"
    ADD_KNOWLEDGE = "add_knowledge"
    SEARCH_KNOWLEDGE = "search_knowledge"
    SHOW_STATUS = "show_status"
    SCHEDULE_TODAY = "schedule_today"
    DAILY_BRIEFING = "daily_briefing"
    UNIVERSITY_SYNC = "university_sync"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    intent: IntentType
    entities: dict = field(default_factory=dict)
    confidence: float = 1.0
    raw_text: str = ""
    source: str = "text"


def _parse_relative_time(match: re.Match) -> datetime:
    """Parse relative time like 'in 2 days'."""
    number = int(match.group(1))
    text = match.group(0).lower()

    if "hour" in text:
        return datetime.now() + timedelta(hours=number)
    elif "minute" in text:
        return datetime.now() + timedelta(minutes=number)
    else:
        return datetime.now() + timedelta(days=number)


def _parse_date(match: re.Match) -> datetime:
    """Parse date like '2024-01-15'."""
    date_str = match.group(1)
    return datetime.strptime(date_str, "%Y-%m-%d")


def _parse_time(match: re.Match) -> datetime:
    """Parse time like '14:30'."""
    time_str = match.group(1)
    parsed = datetime.strptime(time_str, "%H:%M")
    return datetime.now().replace(
        hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0
    )


class IntentParser:
    """Parse natural language into structured intents."""

    PATTERNS = {
        IntentType.ADD_TASK: [
            r"(?:add|create|new)\s+(?:a\s+)?(?:task|todo|task:)\s*(.+)",
            r"(?:remind me to|remember to|don't forget to)\s+(.+)",
            r"^i need to\s+(.+)$",
            r"^todo:\s*(.+)$",
            r"^task:\s*(.+)$",
            r"^task\s+(.+)$",
            r"^remind\s+(.+)$",
        ],
        IntentType.LIST_TASKS: [
            r"what(?:'|)s?\s*(?:on|doing)?\s*(?:my\s+)?(?:task|to ?do|agenda)(?:\s+today)?",
            r"show(?: me)?(?: my)?(?: task| to ?do)?s?(?: today)?",
            r"list(?: me)?(?: my)?(?: task| to ?do)?s?",
            r"do i have(?: any)?(?: task| to ?do)?s?",
            r"what(?:\s+do)?\s+i\s+have(?:\s+to\s+do|\s+today|)?",
            r"^tasks?$",
            r"^todo$",
        ],
        IntentType.COMPLETE_TASK: [
            r"(?:done|finished|complete)(?:d)?\s+(?:task\s+)?(.+)",
            r"(?:mark|set)\s+(.+?)\s+(?:as\s+)?done",
            r"finished\s+(?:with\s+)?(.+)",
            r"^done\s+(.+)$",
            r"^(?:x|check)\s+(.+)$",
        ],
        IntentType.DELETE_TASK: [
            r"(?:delete|remove|cancel)\s+(?:task\s+)?(.+)",
            r"(?:remove|cancel)\s+(.+?)\s+from\s+(?:my\s+)?tasks?",
        ],
        IntentType.ADD_NOTE: [
            r"(?:add|create|new)\s+(?:a\s+)?(?:note|take note|note:)\s*(.*)",
            r"(?:take\s+)?(?:a\s+)?note(?::|\s+on\s+|\s+about\s+)(.+)",
            r"^(?:remember|write down):?\s*(.+)",
            r"^note:\s*(.+)$",
        ],
        IntentType.SEARCH_NOTES: [
            r"(?:search|find)\s+(?:me\s+)?(?:my\s+)?notes?\s+(?:about|for|containing)?\s*(.+)",
            r"(?:what(?:'s| is)\s+)?(?:in|about)\s+(?:my\s+)?notes?\s+(?:about|for)?\s*(.+)",
            r"show\s+(?:me\s+)?(?:my\s+)?notes?\s+about\s+(.+)",
        ],
        IntentType.ADD_KNOWLEDGE: [
            r"(?:remember|keep in mind|note that):?\s*(.+)",
            r"(?:store|save|record)\s+(?:that\s+)?(.+)",
            r"^know:\s*(.+)$",
        ],
        IntentType.SEARCH_KNOWLEDGE: [
            r"(?:what|where)(?:'|)s?\s*(?:my\s+)?(?:knowledge|facts?)(?:\s+about|\s+on)?\s*(.+)",
            r"(?:search|find)\s+(?:my\s+)?knowledge\s+(?:about|for)?\s*(.+)",
            r"(?:do\s+i)?\s*know\s+(?:about)?\s*(.+)",
            r"^i\s+know\s+(?:that|about)\s+(.+)",
        ],
        IntentType.SHOW_STATUS: [
            r"^(?:status|dashboard|summary|overview)$",
            r"(?:how\s+(?:am\s+i|do\s+i\s+look|feels?))?\s*(?:status|dashboard|summary|overview)(?:\s+today)?",
        ],
        IntentType.SCHEDULE_TODAY: [
            r"(?:what(?:'|)s?\s+(?:my|on)\s+)?(?:schedule|agenda|plan)(?:\s+today)?",
            r"(?:plan|schedule)\s+(?:my\s+)?(?:day|today)",
            r"^schedule$",
        ],
        IntentType.DAILY_BRIEFING: [
            r"^(?:briefing|morning|brief)$",
            r"(?:give me a |get |what(?:'|)s my )?(?:daily |morning )?briefing",
            r"(?:what(?:'|)s on |what(?:'|)s up )(?:today|my plate)",
            r"^(?:good morning|morning)$",
        ],
        IntentType.UNIVERSITY_SYNC: [
            r"(?:sync|update|refresh)\s+(?:my\s+)?university",
            r"(?:check|get)\s+(?:my\s+)?(?:assignments?|courses?|grades?)",
            r"(?:sync|check)\s+moodle",
        ],
        IntentType.HELP: [
            r"^(?:help|\?|commands?)",
            r"what\s+can\s+(?:you|i)\s+do",
            r"how\s+(?:do|can)\s+(?:i|you)\s+(?:help|do)",
        ],
    }

    TIME_PATTERNS = [
        (r"tomorrow", datetime.now() + timedelta(days=1)),
        (r"today", datetime.now()),
        (r"next\s+week", datetime.now() + timedelta(days=7)),
        (r"in\s+(\d+)\s+(?:days?|hours?|minutes?)", _parse_relative_time),
        (r"(?:on\s+)?(\d{4}-\d{2}-\d{2})", _parse_date),
        (r"(?:at|by)\s+(\d{1,2}:\d{2})", _parse_time),
    ]

    ENERGY_PATTERNS = [
        (r"(?:high\s+energy|focused?|deep\s+work)", 8),
        (r"(?:medium\s+energy|normal|regular)", 5),
        (r"(?:low\s+energy|easy|simple)", 3),
        (r"energy\s+(?:level\s+)?(\d+)", lambda m: int(m.group(1))),
    ]

    PRIORITY_PATTERNS = [
        (r"(?:urgent|important|critical|ASAP|high\s+priority)", 5),
        (r"(?:medium\s+priority|normal)", 3),
        (r"(?:low\s+priority|whenever|when\s+possible)", 1),
        (r"priority\s+(\d+)", lambda m: int(m.group(1))),
    ]

    def parse(self, text: str, source: str = "text") -> Intent:
        """Parse text into intent."""
        text = text.strip().lower()

        logger.debug(f"Parsing: {text}")

        for intent_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entities = self._extract_entities(text, match)

                    logger.debug(f"Matched intent: {intent_type.value}")

                    return Intent(
                        intent=intent_type,
                        entities=entities,
                        confidence=0.9,
                        raw_text=text,
                        source=source,
                    )

        logger.debug("No intent matched, returning UNKNOWN")
        return Intent(
            intent=IntentType.UNKNOWN,
            entities={"original": text},
            confidence=0.0,
            raw_text=text,
            source=source,
        )

    def _extract_entities(self, text: str, match: re.Match) -> dict:
        """Extract entities from matched text."""
        entities = {}

        if match.groups():
            content = match.group(1) if match.group(1) else text
            entities["content"] = content.strip()

            if "title" not in entities:
                entities["title"] = content.strip()

        for pattern, extractor in self.TIME_PATTERNS:
            time_match = re.search(pattern, text, re.IGNORECASE)
            if time_match:
                if callable(extractor):
                    entities["time"] = extractor(time_match)
                else:
                    entities["time"] = extractor

        for pattern, energy in self.ENERGY_PATTERNS:
            energy_match = re.search(pattern, text, re.IGNORECASE)
            if energy_match:
                if callable(energy):
                    entities["energy_level"] = energy(energy_match)
                else:
                    entities["energy_level"] = energy

        for pattern, priority in self.PRIORITY_PATTERNS:
            priority_match = re.search(pattern, text, re.IGNORECASE)
            if priority_match:
                if callable(priority):
                    entities["priority"] = priority(priority_match)
                else:
                    entities["priority"] = priority

        return entities
