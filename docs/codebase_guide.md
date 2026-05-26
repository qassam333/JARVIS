# JARVIS - Full Codebase & File-by-File Developer Guide 🧠

This guide provides a comprehensive, deep-dive architectural map of the **JARVIS v0.2.0** codebase. It is designed to act as your complete reference manual for understanding, maintaining, and upgrading every single file in the ecosystem.

---

## 🗺️ Codebase Directory Structure

```
JARVIS/
├── config.yaml             # Main configuration file
├── pyproject.toml          # Poetry dependencies and build spec
├── jarvis/
│   ├── main.py             # Main entry point (initializes db)
│   ├── jarvis.py           # Core orchestrator coordinating memory, parser, decision engine
│   ├── cli.py              # Command-line interface built with Click and Rich
│   ├── core/               # Brain, Memory, NLU, and Services registry
│   ├── db/                 # Database layer, migrations, and Pydantic models
│   ├── skills/             # Life-management service layer (Goals, Habits, Tasks, etc.)
│   ├── voice/              # Audio interface, STT (Whisper), TTS (Piper)
│   ├── dashboard/          # FastAPI backend and Vite + React frontend dashboard
│   └── utils/              # Configuration loader and logger
```

---

## 🗂️ Core Entry & CLI Layer

### 1. `jarvis/main.py`
- **Purpose**: Initializes the database and starts the setup logger. Acts as the primary backend-level initialization entry point.
- **Key Lines Explained**:
  - `setup_logger(level=config.log_level, debug=config.debug)` (Line 13): Configures logger levels dynamically from config.
  - `db = Database(config.db_path)` (Line 24): Creates the SQLite DB connection.
  - `db.initialize()` (Line 25): Runs initial migration runner schemas to keep the database up to date.
- **Upgrade Paths**: If adding initialization diagnostics or startup health checks, place them here.

### 2. `jarvis/jarvis.py`
- **Purpose**: Main coordinator class representing the assistant’s brain. Exposes `process(text)` to handle natural language flow.
- **Key Lines Explained**:
  - `self.parser = IntentParser()` (Line 21): Registers the NLU text parser.
  - `self.brain = DecisionEngine()` (Line 22): Sets up routing.
  - `self._setup_handlers()` (Lines 29-69): Registers all handlers for task, note, knowledge, and habit intents.
  - `process(self, text: str, source: str = "text")` (Lines 80-118):
    1. Resolves pronouns/ordinals (`self.memory.resolve_reference(text)`).
    2. Logs the turn into sliding history (`self.memory.session.add_turn`).
    3. Parses and routes the intent (`self.brain.process(intent)`).
    4. Caches the assistant response for future reference resolution.

### 3. `jarvis/cli.py`
- **Purpose**: Click-based Command Line Interface. Translates terminal commands into skill services.
- **Key Components**:
  - `@click.group()` (Line 29): Base command group.
  - `task`, `note`, `know`, `habit`, `goal`, `daily`, `review`, `accountability`: Specific subcommand groupings.
  - **Critical Scoping Fix (Phase 0)**: To avoid shadowing the `date` class, all commands with `--date` options utilize the `today_date` alias (`from datetime import date as today_date`) inside their method scopes.
- **How to Add a Command**:
  1. Define a click function: `@goal.command("my-new-cmd")`
  2. Map options using `@click.option()`.
  3. Load relevant service via `get_services().goals.do_action()`.

---

## 🧠 Core Processing & Memory Layer (`jarvis/core/`)

### 1. `jarvis/core/intent_parser.py`
- **Purpose**: Parses raw natural language inputs into structured `Intent` objects containing intents and parameters.
- **How it Works**:
  - Defines `IntentType` (Enum) for all supported actions.
  - Uses exact keyword prefixes and fuzzy matching algorithms to extract entities like numbers, content titles, or dates.
- **How to Upgrade**: To replace the heuristic NLU with a **local Mistral 7B LLM**, modify the `parse` method to dispatch the string to Ollama instead of fuzzy-matching.

### 2. `jarvis/core/brain.py`
- **Purpose**: Resolves parsed intents to the registered skill handler functions.
- **Key Classes**:
  - `Context`: Stores DB handle and current active user preferences.
  - `Response`: Standardized wrapper containing `success` (bool), `message` (str), and optional `data` (dict).
  - `DecisionEngine`: Maintains registry dict `self.handlers` mapping `IntentType` to functions.

### 3. `jarvis/core/memory.py`
- **Purpose**: Tracks sliding window session turns (capped at 20) and handles reference resolution.
- **How Reference Resolution Works**:
  - When the user lists items, the last generated list (e.g. `[{"id": "abc", "title": "Study"}]`) is cached in `response_data`.
  - If the user follows up with `"complete the first one"`, the engine matches `"first one"`, retrieves `index 0` from history, and replaces `"first one"` with `"abc"`.

### 4. `jarvis/core/services.py`
- **Purpose**: Shared, thread-safe, lazy-initializing service registry. Implements a Singleton pattern.
- **Why it matters**: Ensures multiple CLI calls or dashboard threads access the exact same database pool and skill caches, drastically reducing SQLite locking errors.
- **How to Use**:
  ```python
  from jarvis.core.services import get_services
  services = get_services()
  services.tasks.complete(task_id)
  ```

---

## 💾 Database Layer (`jarvis/db/`)

### 1. `jarvis/db/database.py`
- **Purpose**: Low-level SQLite database adapter wrapper supporting automated migrations.
- **Key Methods**:
  - `query(self, sql, params)`: Executes SQL and formats rows as key-value dictionaries.
  - `execute(self, sql, params)`: Executes write operations, managing commits and rollback safety.

### 2. `jarvis/db/models.py`
- **Purpose**: Pydantic data schemas defining validation rules for API and internal service entities.
- **Key Models**: `Task`, `TaskCreate`, `TaskUpdate`, `Note`, `Knowledge`, `UserProfile`.

### 3. `jarvis/db/migrations/`
- `__init__.py`: Automates migrations. Checks the `_migrations` tracker table in SQLite, loads pending scripts from the `scripts/` directory, and runs `up()` sequentially.
- `scripts/001_initial...`, `002_life_management...`, `003_goal_tasks...`, `004_daily_tasks...`: SQL statements creating the core database tables.

---

## 🛠️ Life Management Skills Layer (`jarvis/skills/`)

### 1. `jarvis/skills/goals.py`
- **Purpose**: Manages hierarchical goals, milestone tracking, and task generation.
- **Key Method**: `generate_tasks(self, goal_id)` (analyzes goal description and generates sequence tasks).

### 2. `jarvis/skills/habits.py`
- **Purpose**: Handles habit tracking, completion logging, and streak calculations.
- **Streak Calculation**: Streak updates are triggered automatically inside `log_habit` and `unlog_habit` using a backwards-looking date traversal.

### 3. `jarvis/skills/daily_tasks.py`
- **Purpose**: Energy-aware daily task selection algorithm.
- **The Formula**:
  - `Priority Score = Priority + Deadline Urgency + Overdue Penalty`
  - Overdue penalty increases score by `3.0` points for every day past deadline.

### 4. `jarvis/skills/schedule.py`
- **Purpose**: Dynamically maps pending tasks to hourly blocks based on the user's available energy (Morning peaks, Evening focus).

### 5. `jarvis/skills/briefing.py`
- **Purpose**: Generates morning briefings.
- **Detailed Timeline Output (Phase 0 Fix)**: Loops over generated schedule slots and structures them:
  ```python
  for slot in schedule.slots:
      time_str = f"{slot.start.strftime('%H:%M')} - {slot.end.strftime('%H:%M')}"
      # Outputs either break slot or task details with [High]/[Low] energy tags
  ```

### 6. `jarvis/skills/accountability.py`
- **Purpose**: Drill-sergeant motivation rules engine. Triggers custom countdown warnings and pushes.

---

## 🔊 Audio & Voice Pipeline (`jarvis/voice/`)

### 1. `jarvis/voice/audio.py`
- **Purpose**: Captures microphone chunks, detects silence, and filters PortAudio device indexes.
- **ALSA Silence Fix (Phase 0)**: Implemented ctypes bindings to `libasound.so.2` on startup to register a dummy handler, completely suppressing standard ALSA warning noise.

### 2. `jarvis/voice/stt.py` & `tts.py`
- **STT**: Translates recorded numpy audio arrays into text strings using **faster-whisper**.
- **TTS**: Takes text, synthesizes a WAV buffer using **Piper ONNX voice**, and plays it via `sounddevice`.

### 3. `jarvis/voice/wake_word.py` & `voice_cli.py`
- **Wake Word**: Continuous low-power listening thread waiting for "Hey Jarvis" or "Hey GG".
- **Reminder Thread (Phase 0 Fix)**:
  Runs `_reminder_loop` in a background thread:
  ```python
  # Checks every minute for active habits with a reminder_time matching current time.
  # If a habit has not been logged today, calls voice.speak() dynamically!
  ```

---

## 🌐 FastAPI & Dashboard Layer (`jarvis/dashboard/`)

### 1. `jarvis/dashboard/backend/main.py`
- **Purpose**: FastAPI web server serving as REST API endpoint for React frontend.
- **REST Endpoints**:
  - `GET /api/profile` (fetches user settings & grad countdown).
  - `GET /api/habits` (habit cards details).
  - `GET /api/goals` (milestone progress metrics).
  - `POST /api/habits/{id}/log` (updates completions).
- **CORS Configuration (Phase 0 Fix)**: Resolves crash by replacing the wildcard `*` with specific allowed dev origins (`localhost:5173`, etc.) when `allow_credentials=True` is active.

### 2. `jarvis/dashboard/frontend/`
- **index.html**: Root wrapper loading `main.jsx`.
- **package.json**: Registers Vite scripts and frontend dependencies (React, Tailwind, PostCSS).
- **src/App.jsx**: Main dashboard view fetching data from local backend endpoints in real time.
- **src/DemoApp.jsx**: Offline high-fidelity mock layout used in `#demo` route for showcasing.

---

## 🔧 Maintenance Checklist & Guide

When performing upgrades or adding new features:

1. **DB Updates**: Never alter tables manually! Create a new migration file under `jarvis/db/migrations/scripts/`, subclass `Migration`, and lazy-load it inside `jarvis/db/migrations/scripts/__init__.py`.
2. **NLU Changes**: To register new voice commands, define the intent type in `IntentType` (`intent_parser.py`), write a routing hook in `handlers.py`, and map it in `_setup_handlers()` (`jarvis.py`).
3. **CORS/Hosting**: If deployment ports or server addresses change, update the origin list inside `jarvis/dashboard/backend/main.py` to match the new endpoints.
4. **Testing**: Run `.venv/bin/pytest` immediately after making edits. Verify that mock database tests run and exit cleanly.
