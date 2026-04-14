# Skills System Documentation

> **Purpose**: Modular, self-contained action handlers that perform specific tasks.

---

## Overview

Skills are the **actions** layer of JARVIS. Each skill:
- Handles specific user requests
- Has clear input/output contracts
- Can be tested independently
- Follows single responsibility principle

```
┌─────────────────────────────────────────────────────────────┐
│                    SKILLS ARCHITECTURE                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Decision Engine (Brain)                │   │
│  │   Routes intents to correct skill                   │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │   Tasks      │ │   Notes      │ │  Knowledge   │      │
│  │   Skill      │ │   Skill      │ │   Skill      │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │  Schedule    │ │ University   │ │  (Future)    │      │
│  │   Skill      │ │   Skill      │ │   Skills     │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
│                                                              │
│  Each skill implements:                                     │
│  • execute(intent, context) -> Response                    │
│  • can_handle(intent) -> bool                              │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
jarvis/
└── skills/
    ├── __init__.py          # Skill registry
    ├── base.py              # Base skill interface
    ├── tasks.py             # Task management skill
    ├── notes.py             # Note-taking skill
    ├── knowledge.py         # Knowledge base skill
    ├── schedule.py          # Scheduling skill
    └── university/          # University scraper
        ├── __init__.py
        ├── base.py          # Abstract scraper interface
        ├── moodle.py        # Moodle implementation
        ├── models.py        # LMS data models
        ├── sync.py          # Sync orchestrator
        └── converter.py     # Convert to JARVIS tasks
```

---

## Base Skill Interface

### The Skill Contract

```python
from abc import ABC, abstractmethod
from jarvis.core.intent_parser import Intent
from jarvis.core.memory import MemoryContext

class Skill(ABC):
    """Base class for all skills"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Skill identifier"""
        pass
    
    @property
    @abstractmethod
    def intents(self) -> list[str]:
        """List of intents this skill handles"""
        pass
    
    @abstractmethod
    def can_handle(self, intent: Intent) -> bool:
        """Check if this skill can handle the intent"""
        pass
    
    @abstractmethod
    def execute(self, intent: Intent, context: MemoryContext) -> "Response":
        """Execute the skill's action"""
        pass
```

### Response Object

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class Response:
    success: bool
    message: str
    data: Any = None
    action_required: str | None = None  # For confirmations
```

---

## Tasks Skill

### Purpose

Manage personal tasks and to-dos with:
- Priority ranking
- Deadline tracking
- Energy level matching
- Source tracking (manual vs university)

### Data Model

```python
@dataclass
class Task:
    id: str                    # UUID
    title: str                 # What to do
    description: str = ""     # Details
    energy_level: int = 5     # 1-10 (energy required)
    deadline: datetime | None = None
    priority: int = 0         # 1-5 (user-set)
    status: str = "pending"   # pending, completed, cancelled
    source: str = "manual"    # manual, moodle, schedule
    created_at: datetime = None
    completed_at: datetime | None = None
```

### Operations

| Operation | Intent | Entities |
|-----------|--------|----------|
| Add task | `add_task` | `title`, `description`, `energy_level`, `deadline`, `priority` |
| List tasks | `query_tasks` | `status`, `date`, `source` |
| Complete task | `complete_task` | `task_id` |
| Edit task | `edit_task` | `task_id`, `title`, `description`, etc. |
| Delete task | `delete_task` | `task_id` |
| Snooze task | `snooze_task` | `task_id`, `new_deadline` |

### CLI Commands

```bash
# Add a task
jarvis task add "Study for math exam" --energy 7 --deadline "2024-01-20"
jarvis task add "Buy groceries" --energy 3

# List tasks
jarvis task list
jarvis task list --status pending
jarvis task list --source moodle

# Complete a task
jarvis task done <task_id>
jarvis task complete "Study for math exam"  # by title

# Edit task
jarvis task edit <task_id> --title "New title" --priority 5

# Delete task
jarvis task delete <task_id>

# Snooze (delay deadline)
jarvis task snooze <task_id> --until "tomorrow"
```

### Priority Scoring Algorithm

Tasks are ranked by urgency score:

```
Score = BaseScore × DeadlineWeight × PriorityWeight × EnergyFit
```

| Component | Weight | Calculation |
|-----------|--------|-------------|
| Base | 1.0 | Starting score |
| Deadline | 2.5x | Closer deadline = higher |
| Priority | 2.0x | User-set priority (1-5) |
| Energy Fit | 1.5x | Match task energy to current energy |

### Energy Matching

```python
def calculate_energy_fit(task_energy: int, current_energy: int) -> float:
    """Returns 0.0 to 1.0 based on how well energies match"""
    diff = abs(task_energy - current_energy)
    if diff <= 2:
        return 1.0
    elif diff <= 4:
        return 0.6
    elif diff <= 6:
        return 0.3
    else:
        return 0.1
```

---

## Notes Skill

### Purpose

Markdown-based note-taking with:
- Tagging system
- Full-text search
- Markdown rendering
- Cross-referencing

### Data Model

```python
@dataclass
class Note:
    id: str
    title: str | None
    content: str              # Markdown content
    tags: list[str] = field(default_factory=list)
    created_at: datetime
    updated_at: datetime
```

### Operations

| Operation | Intent | Entities |
|-----------|--------|----------|
| Add note | `add_note` | `title`, `content`, `tags` |
| List notes | `query_notes` | `tag`, `search` |
| View note | `view_note` | `note_id` |
| Edit note | `edit_note` | `note_id`, `title`, `content`, `tags` |
| Delete note | `delete_note` | `note_id` |
| Search notes | `search_notes` | `query` |

### CLI Commands

```bash
# Add a note
jarvis note add "Meeting Notes" --content "Discussed project timeline"
jarvis note add "Ideas" --tags "brainstorm,project"

# List notes
jarvis note list
jarvis note list --tag work

# Search notes
jarvis note search "meeting"
jarvis note search "python tutorial"

# View a note
jarvis note view <note_id>

# Edit a note
jarvis note edit <note_id> --content "Updated content..."

# Delete note
jarvis note delete <note_id>
```

### Search Implementation

```python
def search_notes(query: str) -> list[Note]:
    """Full-text search across title and content"""
    query_lower = query.lower()
    results = []
    for note in get_all_notes():
        if (query_lower in note.title.lower() or 
            query_lower in note.content.lower() or
            any(query_lower in tag.lower() for tag in note.tags)):
            results.append(note)
    return results
```

---

## Knowledge Skill

### Purpose

Store facts and information for:
- Personal wiki
- API documentation links
- Learned preferences
- Important references

### Data Model

```python
@dataclass
class Knowledge:
    id: str
    fact: str                 # The knowledge piece
    category: str | None     # e.g., "coding", "personal"
    source: str | None       # Where this came from
    tags: list[str] = field(default_factory=list)
    created_at: datetime
```

### Operations

| Operation | Intent | Entities |
|-----------|--------|----------|
| Add knowledge | `add_knowledge` | `fact`, `category`, `source`, `tags` |
| List knowledge | `query_knowledge` | `category`, `tag` |
| Search knowledge | `search_knowledge` | `query` |
| Delete knowledge | `delete_knowledge` | `id` |

### CLI Commands

```bash
# Add knowledge
jarvis know add "Python uses indentation for blocks" --category coding
jarvis know add "Mom's birthday: March 15" --category personal

# List by category
jarvis know list --category coding

# Search
jarvis know search "python"
jarvis know search "birthday"

# Delete
jarvis know delete <id>
```

### Use Cases

1. **API References**: Store useful links
2. **Preferences**: Remember user preferences
3. **Facts**: Important information to recall
4. **Context**: Learned patterns

---

## Schedule Skill

### Purpose

Generate energy-aware daily schedules based on:
- Pending tasks
- Current energy level
- Time available
- Fixed commitments

### Data Model

```python
@dataclass
class Schedule:
    date: date
    slots: list[TimeSlot]
    warnings: list[str]
    
@dataclass
class TimeSlot:
    start: time
    end: time
    task: Task | None
    type: str  # "task", "commitment", "break"
    energy_level: int | None
```

### Scheduling Algorithm

```
┌─────────────────────────────────────────────────────────────┐
│                  SCHEDULING ALGORITHM                        │
│                                                              │
│  INPUT:                                                     │
│  • Pending tasks                                           │
│  • Current energy level (1-10)                            │
│  • Available hours (e.g., 9am-6pm)                        │
│  • Fixed commitments                                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ STEP 1: Filter & Sort                               │   │
│  │ • Remove completed/cancelled tasks                 │   │
│  │ • Score each task (urgency × priority)            │   │
│  │ • Sort by score (highest first)                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ STEP 2: Block Time                                  │   │
│  │ • Add fixed commitments                             │   │
│  │ • Reserve breaks (5 min between tasks)             │   │
│  │ • Mark unavailable slots                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ STEP 3: Allocate Tasks                              │   │
│  │ • Match task energy to available energy             │   │
│  │ • Place high-energy tasks in high-energy slots     │   │
│  │ • Fill remaining slots with medium tasks            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ STEP 4: Validate                                    │   │
│  │ • Check for conflicts                               │   │
│  │ • Check energy exhaustion                           │   │
│  │ • Add warnings if needed                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  OUTPUT: Schedule with warnings                            │
└─────────────────────────────────────────────────────────────┘
```

### Energy Level Handling

```python
ENERGY_SLOTS = {
    "morning_high": (6, 12),     # High energy
    "afternoon_low": (14, 16),   # Low energy (post-lunch dip)
    "evening_recovery": (18, 20) # Medium energy
}

def get_current_energy_level() -> int:
    """Get user's current energy (could be manual or learned)"""
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return 7  # Morning energy
    elif 14 <= hour < 16:
        return 4  # Afternoon dip
    elif 18 <= hour < 22:
        return 5  # Evening
    else:
        return 3  # Night
```

### CLI Commands

```bash
# Generate today's schedule
jarvis schedule today

# Generate schedule for specific date
jarvis schedule generate --date 2024-01-20

# Show only tasks
jarvis schedule tasks

# Show with conflicts
jarvis schedule today --show-conflicts
```

### Conflict Detection

| Conflict Type | Detection | Warning |
|---------------|-----------|---------|
| Time overlap | Slot boundaries intersect | "Back-to-back tasks without break" |
| Energy mismatch | High energy task in low energy slot | "This task may be difficult now" |
| Overload | Total task time > available | "Schedule exceeds recommended hours" |

---

## Skill Registry

### How Skills Are Registered

```python
# jarvis/skills/__init__.py

class SkillRegistry:
    def __init__(self):
        self._skills: dict[str, Skill] = {}
    
    def register(self, skill: Skill):
        for intent in skill.intents:
            self._skills[intent] = skill
    
    def get_skill(self, intent_name: str) -> Skill | None:
        return self._skills.get(intent_name)
    
    def execute(self, intent: Intent, context: MemoryContext) -> Response:
        skill = self.get_skill(intent.intent)
        if not skill:
            return Response(False, f"Unknown intent: {intent.intent}")
        return skill.execute(intent, context)
```

### Using the Registry

```python
from jarvis.skills import SkillRegistry

registry = SkillRegistry()
registry.register(TasksSkill())
registry.register(NotesSkill())
registry.register(KnowledgeSkill())
registry.register(ScheduleSkill())

# In brain.py
def process(intent: Intent) -> Response:
    return registry.execute(intent, memory_context)
```

---

## Adding New Skills

### Example: Weather Skill

```python
# jarvis/skills/weather.py

class WeatherSkill(Skill):
    name = "weather"
    intents = ["query_weather", "weather_forecast"]
    
    def can_handle(self, intent: Intent) -> bool:
        return intent.intent in self.intents
    
    def execute(self, intent: Intent, context: MemoryContext) -> Response:
        location = intent.entities.get("location", "current")
        # Fetch weather data
        weather = self._get_weather(location)
        return Response(
            success=True,
            message=f"Weather in {location}: {weather['temp']}°C, {weather['condition']}",
            data=weather
        )
    
    def _get_weather(self, location: str) -> dict:
        # Weather API implementation
        pass
```

### Register the Skill

```python
# In jarvis/skills/__init__.py
from jarvis.skills.weather import WeatherSkill

registry.register(WeatherSkill())
```

---

## Testing Skills

### Unit Test Example

```python
# tests/test_tasks.py

def test_add_task():
    from jarvis.skills.tasks import TasksSkill
    from jarvis.core.intent_parser import Intent
    
    skill = TasksSkill()
    intent = Intent(
        intent="add_task",
        entities={"title": "Test task", "energy_level": 5}
    )
    
    response = skill.execute(intent, memory_context)
    
    assert response.success is True
    assert "Test task" in response.message
    assert response.data is not None
    assert response.data.title == "Test task"

def test_list_pending_tasks():
    # Add some tasks
    add_task("Task 1")
    add_task("Task 2")
    complete_task("Task 1")
    
    # List pending
    intent = Intent(intent="query_tasks", entities={"status": "pending"})
    response = skill.execute(intent, memory_context)
    
    assert len(response.data) == 1
    assert response.data[0].title == "Task 2"
```

---

<div align="center">

**Skills: Self-contained, testable, extensible.**

</div>
