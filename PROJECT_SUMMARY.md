# JARVIS - Local Second Brain Assistant

> **Privacy-First • Deterministic • Fully Local**

A modular AI assistant inspired by Iron Man's JARVIS. Manages tasks, schedules, knowledge, and integrates with university systems. **No cloud. No telemetry. Your data stays yours.**

---

## Tech Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| **Language** | Python 3.11+ | Rich ecosystem, fast development |
| **Database** | SQLite | Local, portable, encrypted at rest (V2) |
| **CLI** | Rich + Click | Beautiful terminal output |
| **Voice STT** | Whisper.cpp | 100% local, no cloud |
| **Voice TTS** | Piper | Local TTS |
| **Web Scraping** | httpx + BeautifulSoup4 | Async, lightweight |
| **API** | FastAPI (optional) | REST API for web UI |

---

## Upgrades Implemented (Before Phase 1)

| # | Upgrade | Purpose |
|---|---------|---------|
| 1 | **Migration System** | Safely evolve schema without losing data |
| 2 | **Logging Layer** | Debugging, auditing, structured JSON logs |
| 3 | **Validation (Pydantic v2)** | Strict field validation |
| 4 | **API Layer Structure** | REST API for future web UI |
| 5 | **Environment Variables** | Config via env vars for production |
| 6 | **Health Check Endpoint** | System monitoring for Docker |
| 7 | **.gitignore** | Never commit secrets or data |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────┐ │
│  │  CLI/Text   │  │  Voice STT  │  │  REST API   │  │Wake │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                           CORE BRAIN                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ Intent       │───▶│ Memory       │───▶│ Decision     │   │
│  │ Parser       │    │ Engine       │    │ Engine       │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SKILLS (Actions)                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐ │
│  │  Tasks    │  │  Notes    │  │ Knowledge │  │Schedule │ │
│  └───────────┘  └───────────┘  └───────────┘  └─────────┘ │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          UNIVERSITY SCRAPER (Moodle)                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        PERSISTENCE LAYER                     │
│  ┌──────────────────────────────────────────────────────┐ │
│  │   SQLite + Migration System + Encrypted Credentials    │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Mental Model

```
[ INPUT ] → [ INTERPRETATION ] → [ DECISION ] → [ ACTION ]
```

**Build**: INTERPRETATION contract + DECISION engine

---

## Project Structure

```
JARVIS/
├── jarvis/                      # Main package
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   │
│   ├── core/                   # Core brain (TODO)
│   │   ├── brain.py
│   │   ├── memory.py
│   │   └── intent_parser.py
│   │
│   ├── db/                     # Database layer
│   │   ├── database.py         # SQLite connection
│   │   ├── migrations/         # Migration system
│   │   │   ├── __init__.py
│   │   │   └── scripts/
│   │   │       └── __init__.py
│   │   └── encryption.py      # (V2)
│   │
│   ├── skills/                 # Skills/actions (TODO)
│   │   ├── tasks.py
│   │   ├── notes.py
│   │   ├── knowledge.py
│   │   ├── schedule.py
│   │   └── university/
│   │
│   ├── voice/                  # Voice interface (DONE)
│   │   ├── __init__.py
│   │   ├── audio.py           # Audio capture utilities
│   │   ├── stt.py             # Whisper STT
│   │   ├── tts.py             # Piper TTS
│   │   ├── wake_word.py      # Wake word detection
│   │   └── voice_cli.py      # Main voice loop
│   │
│   ├── api/                    # REST API (TODO)
│   │   ├── __init__.py
│   │   └── health.py
│   │
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── config.py           # Config + env vars
│       └── logger.py           # Structured logging
│
├── tests/                      # Unit tests (TODO)
├── data/                      # SQLite DB location
│
├── config.yaml                 # Configuration
├── pyproject.toml              # Dependencies
├── .gitignore                  # Git ignore
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── SKILLS.md
│   ├── UNIVERSITY_INTEGRATION.md
│   ├── VOICE_INTERFACE.md
│   ├── CLI_REFERENCE.md
│   ├── QUICK_START.md
│   ├── MIGRATIONS.md           # NEW
│   ├── LOGGING.md              # NEW
│   ├── API_LAYER.md            # NEW
│   ├── CONFIGURATION.md        # NEW
│   ├── ENVIRONMENT.md          # NEW
│   └── DEPENDENCIES.md         # NEW
│
└── PROJECT_SUMMARY.md          # This file
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_DEBUG` | false | Enable debug mode |
| `JARVIS_DATA_DIR` | ./data | Data directory |
| `JARVIS_DB_PATH` | auto | Database path |
| `JARVIS_LOG_LEVEL` | info | Log level |
| `JARVIS_MASTER_KEY` | - | Encryption key (V2) |
| `JARVIS_VOICE_ENABLED` | false | Enable voice |
| `JARVIS_API_ENABLED` | false | Enable REST API |
| `JARVIS_API_PORT` | 8000 | API port |

**Priority**: ENV > .env > config.yaml > defaults

---

## Implementation Phases

### ✅ Pre-Implementation (DONE)
1. ✅ Project scaffold
2. ✅ Migration system
3. ✅ Logging layer
4. ✅ Configuration with env vars
5. ✅ Health check endpoint
6. ✅ API structure

### Phase 1: Core Foundation (NEXT)
1. Database models
2. Task CRUD
3. CLI interface

### Phase 2: Core Brain
4. Intent parser
5. Decision engine
6. Memory engine

### Phase 3: Skills
7. Notes system
8. Knowledge base
9. Schedule engine

### Phase 4: University Integration
10. Moodle scraper
11. Credential management
12. Task import

### Phase 5: Voice (DONE)
13. Whisper STT - `jarvis/voice/stt.py`
14. Piper TTS - `jarvis/voice/tts.py`
15. Wake word - `jarvis/voice/wake_word.py`
16. Audio utilities - `jarvis/voice/audio.py`
17. Voice CLI - `jarvis/voice/voice_cli.py`

Commands:
- `jarvis voice` - Wake word mode
- `jarvis voice --ptt` - Push-to-talk
- `jarvis voice --continuous` - Continuous listening
- `jarvis voice --test` - Test audio setup

### Phase 6: Deployment (PENDING)
18. Docker
19. Homelab migration

---

## Privacy Guarantees

| Guarantee | Implementation |
|-----------|----------------|
| Zero network calls | No external APIs required |
| No telemetry | Explicitly excluded |
| No cloud | 100% local operation |
| Open source | Full auditable code |
| Secure credentials | Encrypted in V2 |
| Rate limited | Respect servers when scraping |

---

## Getting Started

```bash
# Install
poetry install

# Initialize database
poetry run python -m jarvis.main

# Run CLI
poetry run jarvis --help
```

---

## Dependencies

```toml
python = "^3.11"
pydantic = "^2.0"
pydantic-settings = "^2.0"
sqlalchemy = "^2.0"
cryptography = "^41.0"
pyyaml = "^6.0"
rich = "^13.0"
click = "^8.1"
httpx = "^0.25"
beautifulsoup4 = "^4.12"
```

---

<div align="center">

**Not "Jarvis the Fantasy"**

**But Jarvis that Actually Works.**

**Privacy-First. Deterministic. Yours.**

</div>
