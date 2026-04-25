# JARVIS - Technical Documentation

> **"Build what doesn't change when hardware changes."**

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Brain](#core-brain)
3. [Database Layer](#database-layer)
4. [Skills System](#skills-system)
5. [University Integration](#university-integration)
6. [Voice Interface](#voice-interface)
7. [Privacy & Security](#privacy--security)

---

## Architecture Overview

### The Mental Model

```
┌─────────────────────────────────────────────────────────────┐
│                       INPUT                                  │
│   CLI │ Voice (STT) │ Web Dashboard │ API │ Wake Word       │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    INTERPRETATION                            │
│   Intent Parser → Extract intent + entities from input      │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DECISION                                │
│   Decision Engine → Route intent to correct skill/action    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       ACTION                                 │
│   Execute skill → Return response to user                   │
└─────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

| Layer | Purpose | Why Separated |
|-------|---------|---------------|
| **Interpretation** | Convert raw input to structured intent | Hardware can change (voice → text → API) |
| **Decision** | Route to correct handler | Business logic stays stable |
| **Action** | Execute the actual work | Can swap implementations |

**Key Principle**: The **Decision Engine** and **Contracts** are the most stable parts. They outlive:
- STT engines (Whisper → Vosk → etc.)
- TTS engines (Piper → Coqui → etc.)
- NLP models (Rule-based → LLM → etc.)
- Device integrations (MQTT → Home Assistant → etc.)

---

## Core Brain

### 1. Intent Parser (`jarvis/core/intent_parser.py`)

**Purpose**: Convert natural language/text into structured intent objects.

#### What It Does
- Receives raw user input
- Extracts **intent type** (what user wants)
- Extracts **entities** (specific details)
- Returns structured `Intent` object

#### Example

```
Input:  "remind me to study math tomorrow at 9am"
Output: Intent(
    intent="add_task",
    entities={
        "title": "study math",
        "deadline": "2024-01-16T09:00:00",
        "source": "voice"
    },
    confidence=0.92
)
```

#### Implementation Strategy

**V1 (Rule-Based + Fuzzy Matching)**: Primary pattern matching with regex, fallback to fuzzy keyword scoring.
```python
# Primary Regex Matching
PATTERNS = {
    "add_task": [
        r"remind me to (?P<title>.*)",
        r"add task (?P<title>.*)",
    ]
}

# Fallback Fuzzy Matching
INTENT_KEYWORDS = {
    "add_task": ["add", "create", "new", "task", "todo", "remind"]
}
```

#### Why Not Use an LLM?
1. **Speed**: Pattern matching and fuzzy scoring is instant
2. **Privacy**: No model inference needed
3. **Determinism**: Same input = same output always
4. **Simplicity**: Easier to debug and maintain

---

### 2. Decision Engine (`jarvis/core/brain.py`)

**Purpose**: Route intents to correct handlers and coordinate responses.

#### What It Does
- Receives structured `Intent` from parser
- Validates intent against contracts
- Determines which skill handles it
- Executes skill action
- Returns formatted response

#### Flow Diagram

```
┌─────────────┐
│  Intent     │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────────┐
│  Validate   │────▶│ Invalid?        │
│  Contract   │     │ → Return error  │
└──────┬──────┘     └─────────────────┘
       │ Valid
       ▼
┌─────────────┐
│  Route to   │
│  Skill      │
└──────┬──────┘
       │
       ├────────────────────────────────────┐
       │                                    │
       ▼                                    ▼
┌─────────────┐                    ┌─────────────┐
│ Task Skill  │                    │ Note Skill  │
└──────┬──────┘                    └──────┬──────┘
       │                                    │
       ▼                                    ▼
┌─────────────┐                    ┌─────────────┐
│  Execute    │                    │  Execute    │
│  Action    │                    │  Action     │
└──────┬──────┘                    └──────┬──────┘
       │                                    │
       └────────────────┬─────────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │  Format        │
               │  Response      │
               └─────────────────┘
```

#### Decision Rules Example

```python
RULES = {
    "add_task": {
        "required_entities": ["title"],
        "optional_entities": ["deadline", "priority", "energy_level"],
        "handler": "tasks.add",
        "response_template": "Task '{title}' added. I'll remind you {reminder}."
    },
    "query_tasks": {
        "required_entities": [],
        "optional_entities": ["date", "status"],
        "handler": "tasks.query",
        "response_template": "You have {count} tasks: {list}"
    }
}
```

#### Why This Approach?

| Benefit | Explanation |
|---------|-------------|
| **Explainable** | Every decision can be traced |
| **Debuggable** | Easy to see why X happened |
| **Testable** | Pure functions, no side effects |
| **Extensible** | Add new intents by adding rules |

---

### 3. Memory Engine (`jarvis/core/memory.py`)

**Purpose**: Maintain context across conversations and sessions.

#### What It Does
- Stores conversation history (short-term)
- Tracks user preferences learned over time
- Maintains current session context
- Provides context to decision engine

#### Memory Types

| Type | Duration | Content |
|------|----------|---------|
| **Session** | Current session | Recent commands, current task being discussed |
| **User Profile** | Permanent | Preferences, habits, energy patterns |
| **Daily Context** | Daily reset | Today's energy level, completed tasks |

#### Example State

```python
class MemoryContext:
    session: SessionContext
    user: UserProfile
    daily: DailyContext

class SessionContext:
    recent_commands: List[Command]
    current_topic: str | None  # "task", "note", "university"
    pending_confirmation: Action | None
    last_result: Any

class UserProfile:
    name: str
    timezone: str
    default_energy: int
    preferred_response_style: str  # "brief", "detailed"

class DailyContext:
    date: date
    energy_level: int  # 1-10
    tasks_completed: int
    mood: str | None
```

#### Why Memory Matters

Without memory:
```
User: "remind me to call mom"
Jarvis: "Done! Call mom scheduled."
User: "when?"
Jarvis: "I don't know what you mean."
```

With memory:
```
User: "remind me to call mom"
Jarvis: "Done! Call mom scheduled."
User: "when?"
Jarvis: "You didn't specify a time. When should I remind you?"
User: "5pm"
Jarvis: "I'll remind you at 5pm today."
```

---

## Database Layer

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│         (Tasks, Notes, Knowledge, University)                │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    ORM Layer (SQLAlchemy)                    │
│         Models → Database Operations                         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Encryption Layer (Fernet)                    │
│        Encrypt/Decrypt sensitive fields                     │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                           │
│                  Single file, portable                       │
└─────────────────────────────────────────────────────────────┘
```

### Why SQLite?

| Pros | Cons (and mitigations) |
|------|----------------------|
| Single file, easy backup | Single writer (fine for personal use) |
| Zero configuration | Limited concurrency (OK for CLI) |
| Works offline | Not for multi-user (N/A) |
| Portable (copy file = backup) | - |
| Fast for read-heavy workloads | - |

### Why Not PostgreSQL/MySQL?

- **Your paranoia**: No server to maintain, no network exposure
- **Simplicity**: One file = one backup
- **Portability**: Move JARVIS by copying folder
- **Privacy**: Data never in external database

### Encryption Layer (`jarvis/db/encryption.py`)

**Purpose**: Protect sensitive data at rest.

#### What Gets Encrypted

| Field | Why Encrypted |
|-------|---------------|
| University passwords | Critical credentials |
| Session tokens | Access tokens |
| User notes (optional) | Personal data |

#### How Fernet Works

```python
from cryptography.fernet import Fernet

# Generate key (done once, stored securely)
key = Fernet.generate_key()
fernet = Fernet(key)

# Encrypt
encrypted = fernet.encrypt(b"my_password")

# Decrypt
decrypted = fernet.decrypt(encrypted)
```

#### Key Management

```
┌─────────────────────────────────────────┐
│           Master Key                     │
│   Generated once, stored in config.yaml  │
│   OR: User-provided at first run        │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│        Key Derivation                    │
│   PBKDF2 → 32-byte Fernet key           │
└─────────────────────────────────────────┘
```

**Note**: The master key itself is not encrypted. For maximum paranoia:
- Store in encrypted config
- Use system keyring (future enhancement)

---

## Skills System

### What Are Skills?

Skills are **self-contained modules** that perform specific tasks. Each skill:
- Has clear input/output contracts
- Can be tested independently
- Can be enabled/disabled
- Follows single responsibility principle

### Skill Interface

```python
class Skill(ABC):
    name: str
    intents: list[str]  # Intents this skill handles
    
    @abstractmethod
    def execute(self, intent: Intent, context: MemoryContext) -> Response:
        """Execute the skill's action"""
        pass
    
    @abstractmethod
    def can_handle(self, intent: Intent) -> bool:
        """Check if this skill handles the intent"""
        pass
```

### Built-in Skills

#### 1. Tasks Skill (`jarvis/skills/tasks.py`)

**Purpose**: Manage personal tasks and to-dos.

##### Data Model

```python
class Task:
    id: str              # UUID
    title: str           # What to do
    description: str     # Optional details
    energy_level: int    # 1-10 (energy required)
    deadline: datetime   # Optional due date
    priority: int        # 1-5 (user-set)
    status: str          # pending | completed | cancelled
    source: str          # manual | moodle | schedule
    created_at: datetime
    completed_at: datetime | None
```

##### Operations

| Operation | CLI Command | Description |
|-----------|-------------|-------------|
| Add | `jarvis task add "..."` | Create new task |
| List | `jarvis task list` | Show all pending tasks |
| Complete | `jarvis task done <id>` | Mark task as done |
| Delete | `jarvis task delete <id>` | Remove task |
| Edit | `jarvis task edit <id> --title "..."` | Modify task |

##### Priority Scoring

Tasks are ranked by urgency score:

```
Score = (Deadline Weight) × (Importance) × (Energy Fit)
```

| Factor | Weight | Explanation |
|--------|--------|-------------|
| Deadline | 2.5x | Closer = higher score |
| Priority | 2.0x | User-set priority |
| Energy Fit | 1.5x | Match task energy to current energy |

#### 2. Notes Skill (`jarvis/skills/notes.py`)

**Purpose**: Markdown-based note-taking with search.

##### Data Model

```python
class Note:
    id: str
    title: str
    content: str         # Markdown content
    tags: list[str]     # For categorization
    created_at: datetime
    updated_at: datetime
```

##### Features

- **Markdown support**: Full MD rendering
- **Tagging**: Organize notes by topic
- **Full-text search**: Search in title + content
- **Linking**: Connect related notes

##### Operations

| Operation | CLI Command |
|-----------|-------------|
| Create | `jarvis note add "Title" --content "..."` |
| List | `jarvis note list --tag work` |
| Search | `jarvis note search "keyword"` |
| View | `jarvis note view <id>` |
| Edit | `jarvis note edit <id> --title "..."` |
| Delete | `jarvis note delete <id>` |

#### 3. Knowledge Skill (`jarvis/skills/knowledge.py`)

**Purpose**: Store facts, references, and learned information.

##### Data Model

```python
class Knowledge:
    id: str
    fact: str            # The knowledge piece
    category: str        # e.g., "science", "personal", "coding"
    source: str          # Where this came from
    tags: list[str]
    created_at: datetime
```

##### Use Cases

- Store API documentation links
- Remember user preferences
- Keep track of important facts
- Build a personal wiki

##### Operations

| Operation | CLI Command |
|-----------|-------------|
| Add | `jarvis know add "Python uses whitespace" --category coding` |
| List | `jarvis know list --category coding` |
| Search | `jarvis know search "python"` |
| Delete | `jarvis know delete <id>` |

#### 4. Schedule Skill (`jarvis/skills/schedule.py`)

**Purpose**: Generate daily schedules based on tasks and energy.

##### Energy-Aware Scheduling

The scheduler considers your **current energy level**:

```
Energy Levels:
1-3  = Low (simple tasks, admin work)
4-6  = Medium (normal work)
7-10 = High (complex tasks, deep work)
```

##### Schedule Generation Algorithm

```
1. INPUT: Tasks + Energy Level + Time Available
          │
          ▼
2. FILTER: Remove completed/archived tasks
          │
          ▼
3. SCORE: Rank by urgency × priority × energy fit
          │
          ▼
4. BLOCK: Allocate time slots
          │
          ▼
5. BUFFER: Add 5-minute transitions
          │
          ▼
6. OUTPUT: Structured daily schedule
```

##### Conflict Detection

| Conflict Type | Detection | Resolution |
|---------------|-----------|------------|
| Time overlap | Check slot boundaries | Reorder tasks |
| Energy mismatch | High energy task in low energy slot | Reschedule |
| Overload | Total time > available | Mark as warning |

---

## University Integration

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              University Scraper System                       │
│                                                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Base      │────│   Moodle    │────│   Future    │   │
│  │   Interface │    │   Scraper   │    │   Adapters  │   │
│  └─────────────┘    └─────────────┘    └─────────────┘   │
│         │                  │                               │
│         ▼                  ▼                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Sync Orchestrator                       │   │
│  │   - Fetches from LMS                                │   │
│  │   - Deduplicates                                    │   │
│  │   - Converts to tasks                               │   │
│  │   - Notifies user                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                │
│         ▼                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Credential Manager                          │   │
│  │   - Encrypted storage                               │   │
│  │   - Session management                              │   │
│  │   - Secure logout                                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Why Strategy Pattern?

```python
class UniversityScraper(ABC):
    """Abstract base - swap implementations without changing core"""
    
    @abstractmethod
    def authenticate(self, credentials: Credentials) -> Session:
        pass
    
    @abstractmethod
    def get_courses(self, session: Session) -> List[Course]:
        pass
    
    @abstractmethod
    def get_assignments(self, session: Session, course_id: str) -> List[Assignment]:
        pass
```

**Benefits**:
- Add Canvas/Blackboard support by implementing interface
- Test without real LMS (mock implementation)
- Swap scraper without touching rest of code

### Supported Assignment Types

| Type | Source | Mapped To |
|------|--------|-----------|
| `assignment` | Moodle Assignment | JARVIS Task |
| `quiz` | Moodle Quiz | JARVIS Task (with time limit) |
| `exam` | Moodle Exam | JARVIS Task (high priority) |
| `lecture` | Moodle Event | JARVIS Commitment |

### Sync Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                     DAILY SYNC CYCLE                         │
│                                                              │
│  1. Trigger (scheduled or manual)                           │
│              │                                              │
│              ▼                                              │
│  2. Decrypt credentials                                      │
│              │                                              │
│              ▼                                              │
│  3. Login to LMS                                             │
│              │                                              │
│              ▼                                              │
│  4. Fetch courses                                            │
│              │                                              │
│              ▼                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ For each course:                                     │   │
│  │   • Rate limit (1 req/2 sec)                        │   │
│  │   • Fetch assignments                               │   │
│  │   • Fetch quizzes                                   │   │
│  │   • Fetch upcoming events                          │   │
│  └─────────────────────────────────────────────────────┘   │
│              │                                              │
│              ▼                                              │
│  5. Deduplicate (by LMS ID)                                 │
│              │                                              │
│              ▼                                              │
│  6. Convert to JARVIS tasks                                 │
│              │                                              │
│              ▼                                              │
│  7. Store in database                                       │
│              │                                              │
│              ▼                                              │
│  8. Log sync result                                         │
│              │                                              │
│              ▼                                              │
│  9. Secure logout                                           │
└─────────────────────────────────────────────────────────────┘
```

### Security Measures

| Measure | Implementation |
|---------|----------------|
| Encrypted credentials | Fernet (AES) |
| Session expiry | Tokens invalidated after 24h |
| Rate limiting | Max 1 request/2 seconds |
| Secure storage | Credentials never logged |
| Error handling | Graceful failure, manual fallback |
| Data minimization | Only deadlines/types, no grades |

---

## Voice Interface

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    VOICE PIPELINE                            │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Wake Word  │───▶│     STT      │───▶│   Parser     │  │
│  │  Detection   │    │   (Whisper) │    │   (Intent)   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                                        │          │
│         │                                        ▼          │
│         │                               ┌──────────────┐    │
│         │                               │   Decision   │    │
│         │                               │   Engine     │    │
│         │                               └──────────────┘    │
│         │                                        │          │
│         │                                        ▼          │
│         │                               ┌──────────────┐    │
│         │                               │     TTS      │    │
│         │                               │   (Piper)    │    │
│         │                               └──────────────┘    │
│         │                                        │          │
│         ▼                                        ▼          │
│  ┌──────────────┐                       Audio Output      │
│  │   Microphone │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

### 1. Wake Word Detection (`jarvis/voice/wake_word.py`)

**Purpose**: Detect when user says "Hey JARVIS".

#### Implementation Options

| Library | Pros | Cons |
|---------|------|------|
| **Porcupine** | Accurate, fast | Requires license for commercial |
| **Snowboy** | Open source | Deprecated |
| **Picovoice** | Free for personal | Rate limited |
| **Custom (VAD)** | Full control | More development |

#### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    WAKE WORD FLOW                            │
│                                                              │
│  ┌────────────┐                                             │
│  │  Audio     │ (continuous stream from mic)                 │
│  │  Stream    │                                             │
│  └─────┬──────┘                                             │
│        │                                                    │
│        ▼                                                    │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐        │
│  │ Voice      │───▶│ Keyword    │───▶│ "Hey       │        │
│  │ Activity   │    │ Detection  │    │  JARVIS"?  │        │
│  │ Detection  │    │            │    │            │        │
│  └────────────┘    └────────────┘    └──────┬─────┘        │
│                                             │              │
│                                             ▼              │
│                                    ┌────────────┐         │
│                                    │ Triggered! │         │
│                                    │ Start      │         │
│                                    │ recording  │         │
│                                    └────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

#### Privacy Considerations

| Option | Privacy | Convenience |
|--------|---------|------------|
| Always listening | Lower | Highest |
| Push-to-talk | Highest | Lower |

**Recommendation**: Start with wake word, add PTT as backup option.

### 2. Speech-to-Text (`jarvis/voice/stt.py`)

**Technology**: Whisper.cpp

#### Why Whisper.cpp?

| Feature | Benefit |
|---------|---------|
| 100% local | No data to cloud |
| Multiple languages | Arabic support |
| Various sizes | Balance speed/accuracy |
| CPU inference | No GPU required |

#### Model Sizes

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | 39 MB | ~10x realtime | Good |
| base | 74 MB | ~5x realtime | Better |
| small | 244 MB | ~2x realtime | Excellent |
| medium | 769 MB | ~1x realtime | Best |

**Recommendation for your 16GB RAM**: `base` model (fast, accurate enough)

### 3. Text-to-Speech (`jarvis/voice/tts.py`)

**Technology**: Piper

#### Why Piper?

| Feature | Benefit |
|---------|---------|
| 100% local | Privacy preserved |
| Fast inference | Real-time capable |
| Multiple voices | Custom voice later |
| Low resource | Runs on CPU |

#### Features

- Multiple voice options
- Adjustable speaking rate
- Emotion/tone control (future)

### Voice Command Examples

```
┌─────────────────────────────────────────────────────────────┐
│                    VOICE COMMANDS                           │
│                                                              │
│  "Hey JARVIS, remind me to study math"                      │
│  → Creates task with title="study math"                    │
│                                                              │
│  "Hey JARVIS, what do I have today?"                        │
│  → Lists today's tasks                                      │
│                                                              │
│  "Hey JARVIS, add a note about the meeting"                 │
│  → Creates note with title="meeting notes"                  │
│                                                              │
│  "Hey JARVIS, sync my university"                           │
│  → Triggers Moodle sync                                     │
│                                                              │
│  "Hey JARVIS, good morning"                                 │
│  → Morning briefing (tasks, weather, schedule)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Privacy & Security

### Guiding Principles

1. **Data minimization**: Store only what's needed
2. **Zero trust**: Assume hostile environment
3. **Defense in depth**: Multiple security layers
4. **Transparency**: No hidden services

### Security Matrix

| Concern | Solution | Layer |
|---------|----------|-------|
| Credential theft | Fernet encryption | Database |
| Network sniffing | Local-only operation | Architecture |
| Data theft | Encrypted storage | Database |
| Session hijacking | Short-lived tokens | University |
| Unwanted recording | User-controlled wake word | Voice |
| Privacy leaks | No telemetry | Application |

### Data Flow Security

```
┌─────────────────────────────────────────────────────────────┐
│                   DATA SECURITY FLOW                        │
│                                                              │
│  User Input ──────────────────────────────────────────────▶│
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ INPUT VALIDATION                                     │   │
│  │ • Sanitize all inputs                                │   │
│  │ • Type checking (Pydantic)                          │   │
│  │ • Length limits                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ENCRYPTION (Sensitive Data)                          │   │
│  │ • University passwords: Fernet                       │   │
│  │ • Session tokens: Fernet                            │   │
│  │ • Future: Full disk encryption                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ DATABASE (SQLite)                                     │   │
│  │ • File permissions: user only                       │   │
│  │ • Location: user-controlled                         │   │
│  │ • Backup: manual/user-driven                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  Storage ───────────────────────────────────────────────▶ │
└─────────────────────────────────────────────────────────────┘
```

### What JARVIS Does NOT Do

| ❌ Never | Why |
|----------|-----|
| Send data to cloud | Privacy |
| Call home/phone home | No telemetry |
| Log sensitive data | Security |
| Use non-local AI | Privacy |
| Require internet | Offline capable |
| Share data | User owns everything |

---

## Dependencies Explanation

### Core Dependencies

| Package | Purpose | Why Needed |
|---------|---------|------------|
| `pydantic` | Data validation | Type-safe models |
| `sqlalchemy` | ORM | Database operations |
| `cryptography` | Encryption | Secure credential storage |
| `rich` | CLI formatting | Beautiful terminal output |
| `click` | CLI framework | Command parsing |
| `pyyaml` | Config files | Human-readable config |

### Optional Dependencies

| Package | Purpose | Why Optional |
|---------|---------|--------------|
| `httpx` | HTTP client | Only for university scraping |
| `beautifulsoup4` | HTML parsing | Only for LMS scraping |
| `whispercpp` | STT | Only for voice |
| `piper` | TTS | Only for voice |

---

## Future Enhancements (V2+)

### Already Planned

- [ ] Ollama integration for natural language queries
- [ ] Docker deployment for homelab
- [ ] System keyring integration
- [ ] Habit tracking
- [ ] Progress analytics

### Possible Additions

- [ ] Encrypted sync between devices
- [ ] Multi-user support
- [ ] Plugin system for custom skills
- [ ] Web UI dashboard
- [ ] Mobile companion app

---

## Glossary

| Term | Definition |
|------|------------|
| **Intent** | What the user wants to do |
| **Entities** | Specific details extracted from input |
| **Skill** | Self-contained module that performs actions |
| **Wake Word** | Phrase that activates voice listening |
| **STT** | Speech-to-text conversion |
| **TTS** | Text-to-speech synthesis |
| **Fernet** | Symmetric encryption (AES-128-CBC) |
| **LMS** | Learning Management System (Moodle, Canvas, etc.) |

---

<div align="center">

**Built with Privacy in Mind**

**Deterministic • Explainable • Yours**

</div>
