"""Intent parser for natural language understanding."""

import re
from difflib import SequenceMatcher
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
    LOG_HABIT = "log_habit"
    LIST_HABITS = "list_habits"
    GOAL_STATUS = "goal_status"
    SET_ENERGY = "set_energy"
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
            r"^i have to\s+(.+)$",
            r"^i should\s+(.+)$",
            r"^put\s+(.+?)\s+on\s+(?:my\s+)?(?:task|to ?do)\s+list$",
        ],
        IntentType.LIST_TASKS: [
            r"what(?:'|)s?\s*(?:on|doing)?\s*(?:my\s+)?(?:task|to ?do|agenda)(?:\s+today)?",
            r"show(?: me)?(?: my)?(?:\s+(?:task|to ?do)s?)(?:\s+today)?",
            r"list(?: me)?(?: my)?(?: task| to ?do)?s?",
            r"do i have(?: any)?(?: task| to ?do)?s?",
            r"what(?:\s+do)?\s+i\s+have(?:\s+to\s+do|\s+today|)?",
            r"^tasks?$",
            r"^todo$",
            r"any\s+(?:tasks?|deadlines?|things?)\s+(?:to\s+do|today|pending)?",
            r"what(?:'|)s\s+(?:left|pending|remaining)",
            r"what\s+should\s+i\s+(?:do|work\s+on|focus\s+on)",
        ],
        IntentType.COMPLETE_TASK: [
            r"(?:done|finished|complete)(?:d)?\s+(?:task\s+)?(.+)",
            r"(?:mark|set)\s+(.+?)\s+(?:as\s+)?done",
            r"finished\s+(?:with\s+)?(.+)",
            r"^done\s+(.+)$",
            r"^(?:x|check)\s+(.+)$",
            r"i(?:'ve| have)?\s+(?:finished|completed|done)\s+(.+)",
            r"(?:cross|tick|check)\s+(?:off\s+)?(.+)",
        ],
        IntentType.DELETE_TASK: [
            r"(?:delete|remove|cancel)\s+(?:task\s+)?(.+)",
            r"(?:remove|cancel)\s+(.+?)\s+from\s+(?:my\s+)?tasks?",
            r"drop\s+(.+)",
        ],
        IntentType.ADD_NOTE: [
            r"(?:add|create|new)\s+(?:a\s+)?(?:note|take note|note:)\s*(.*)",
            r"(?:take\s+)?(?:a\s+)?note(?::|\s+on\s+|\s+about\s+)(.+)",
            r"^(?:remember|write down):?\s*(.+)",
            r"^note:\s*(.+)$",
            r"^jot\s+down\s+(.+)$",
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
            r"how(?:'s|\s+is)\s+(?:my|everything|things?)",
        ],
        IntentType.SCHEDULE_TODAY: [
            r"(?:what(?:'|)s?\s+(?:my|on)\s+)?(?:schedule|agenda|plan)(?:\s+today)?",
            r"(?:plan|schedule)\s+(?:my\s+)?(?:day|today)",
            r"^schedule$",
            r"plan\s+(?:out\s+)?my\s+day",
        ],
        IntentType.DAILY_BRIEFING: [
            r"^(?:briefing|morning|brief)$",
            r"(?:give me a |get |what(?:'|)s my )?(?:daily |morning )?briefing",
            r"(?:what(?:'|)s on |what(?:'|)s up )(?:today|my plate)",
            r"^(?:good morning|morning)$",
            r"catch\s+me\s+up",
            r"what(?:'|)s\s+(?:new|happening)",
        ],
        IntentType.LOG_HABIT: [
            r"(?:log|track|did|done|completed?|checked?)\s+(?:my\s+)?(.+?)\s*(?:habit|today)?$",
            r"i\s+(?:did|finished|completed)\s+(?:my\s+)?(.+?)\s*(?:today)?$",
            r"(?:mark|check)\s+(?:off\s+)?(?:my\s+)?(.+?)\s+(?:habit|as\s+done)",
            r"^(?:log|track)\s+habit\s+(.+)$",
            r"(?:habit|check)\s+(.+?)\s+done$",
        ],
        IntentType.LIST_HABITS: [
            r"(?:show|list|what(?:'|)s?)\s+(?:my\s+)?habits?",
            r"(?:habit|habits?)\s*(?:list|status|streaks?|tracker?)?",
            r"^habits?$",
            r"how\s+(?:are|is)\s+my\s+(?:habits?|streaks?)",
            r"(?:any\s+)?(?:habit|streak)\s+(?:warnings?|alerts?)",
        ],
        IntentType.GOAL_STATUS: [
            r"(?:show|list|what(?:'|)s?)\s+(?:my\s+)?goals?",
            r"(?:how(?:'s|\s+is)|what(?:'s|\s+is))\s+(?:my\s+)?(.+?)\s+goal",
            r"goal\s+(?:progress|status|list)",
            r"^goals?$",
            r"how\s+(?:am\s+i\s+doing|is\s+my\s+progress)\s+(?:on|with)\s+(.+)",
        ],
        IntentType.SET_ENERGY: [
            r"(?:my\s+)?energy(?:\s+(?:level\s+)?(?:is|=)?)?\s*(\d+)",
            r"(?:set|update)\s+(?:my\s+)?energy\s+(?:to\s+)?(\d+)",
            r"(?:i(?:'m| am)\s+)?(?:feeling\s+)?energy\s+(\d+)",
            r"energy\s+(high|medium|low)",
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

    # Keyword sets for fuzzy matching fallback
    INTENT_KEYWORDS = {
        IntentType.ADD_TASK: ["add", "create", "new", "task", "todo", "remind", "need", "should", "must"],
        IntentType.LIST_TASKS: ["list", "show", "tasks", "todo", "pending", "what", "have", "doing", "left"],
        IntentType.COMPLETE_TASK: ["done", "finished", "complete", "mark", "check", "crossed"],
        IntentType.DELETE_TASK: ["delete", "remove", "cancel", "drop"],
        IntentType.ADD_NOTE: ["note", "jot", "write", "record"],
        IntentType.SEARCH_NOTES: ["search", "find", "notes", "look"],
        IntentType.SHOW_STATUS: ["status", "dashboard", "summary", "overview", "how"],
        IntentType.SCHEDULE_TODAY: ["schedule", "agenda", "plan", "day"],
        IntentType.DAILY_BRIEFING: ["briefing", "morning", "brief", "catch", "update", "new", "happening"],
        IntentType.LOG_HABIT: ["log", "habit", "track", "tracked", "checked", "exercise", "meditation", "reading"],
        IntentType.LIST_HABITS: ["habits", "streak", "streaks", "tracker"],
        IntentType.GOAL_STATUS: ["goal", "goals", "progress", "milestone"],
        IntentType.SET_ENERGY: ["energy", "level", "feeling"],
        IntentType.HELP: ["help", "commands", "what", "can"],
    }

    TIME_PATTERNS = [
        (r"tomorrow", lambda m: datetime.now() + timedelta(days=1)),
        (r"today", lambda m: datetime.now()),
        (r"next\s+week", lambda m: datetime.now() + timedelta(days=7)),
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

        # Phase 1: Exact regex matching (high confidence)
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

        # Phase 2: Fuzzy keyword matching fallback
        fuzzy_result = self._fuzzy_match(text)
        if fuzzy_result:
            intent_type, confidence = fuzzy_result
            logger.debug(f"Fuzzy matched intent: {intent_type.value} (confidence: {confidence:.2f})")
            return Intent(
                intent=intent_type,
                entities={"content": text, "title": text},
                confidence=confidence,
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

    def _fuzzy_match(self, text: str) -> tuple:
        """Fuzzy keyword matching fallback.

        Computes similarity between input tokens and keyword sets per intent type.
        Returns (IntentType, confidence) if best score > threshold, else None.
        """
        words = set(re.findall(r'\w+', text.lower()))
        if not words:
            return None

        best_intent = None
        best_score = 0.0

        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            # Direct keyword overlap
            overlap = words & set(keywords)
            overlap_score = len(overlap) / max(len(keywords), 1)

            # Fuzzy token-level matching for close misspellings
            fuzzy_score = 0.0
            for word in words:
                for keyword in keywords:
                    ratio = SequenceMatcher(None, word, keyword).ratio()
                    if ratio > 0.8:  # Close enough match
                        fuzzy_score += ratio

            fuzzy_score = fuzzy_score / max(len(keywords), 1)

            # Combined score
            combined = (overlap_score * 0.7) + (fuzzy_score * 0.3)

            if combined > best_score:
                best_score = combined
                best_intent = intent_type

        # Only return if above threshold
        if best_score > 0.15 and best_intent:
            # Map to confidence range 0.5-0.75
            confidence = min(0.75, 0.5 + best_score * 0.5)
            return (best_intent, confidence)

        return None

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
