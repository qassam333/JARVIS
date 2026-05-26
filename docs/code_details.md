# JARVIS - Deep Code Walkthrough & Line-by-Line Developer Guide 🔍

This document provides a highly detailed, line-by-line and logic-by-logic walkthrough of the core files in the **JARVIS** codebase. It explains the precise algorithms, variable evaluations, SQL queries, and architectural designs of each critical file to ensure seamless future development.

---

## 🧠 Core Processing & NLU Engine (`jarvis/core/`)

### 1. `jarvis/core/intent_parser.py`
This file parses natural language queries from the terminal or microphone into structured `Intent` datastructures.

#### Logic Walkthrough:
- **`IntentType` Class (Lines 10-25)**:
  An Enum defining all primary intents. Examples:
  - `ADD_TASK`: Adding standard tasks.
  - `LOG_HABIT`: Logging habit completion.
  - `GOAL_STATUS`: Reading milestone status.
  - `DAILY_BRIEFING`: Generating the morning briefing.
- **`Intent` Dataclass (Lines 28-35)**:
  Represents a parsed query. Contains:
  - `intent`: The resolved `IntentType`.
  - `entities`: A dictionary of parameters (e.g., `title`, `priority`, `time`, `pages`).
  - `confidence`: Match float from `0.0` to `1.0`.
  - `raw_text`: Cleaned lowercased input text.
- **`IntentParser.parse(self, text, source)` (Lines 40-80)**:
  1. Cleans input (lowercasing, trimming whitespace).
  2. Runs custom keyword prefix matching. For example:
     - If text starts with `"add task"`, `"todo"`, `"remind me to"`, it resolves to `IntentType.ADD_TASK` and extracts the remaining text as the `title` entity.
     - If text starts with `"log habit"`, `"done habit"`, it parses the string, extracting habit name/ID, optional pages (`--pages X`), and duration (`--duration Y`).
  3. If no prefix matches, runs a **Fuzzy Jaro-Winkler Similarity** search against pre-defined intent trigger keywords (like `"briefing"`, `"schedule"`, `"sync"`, `"status"`).
  4. Returns the `Intent` object with appropriate confidence.

---

### 2. `jarvis/core/brain.py`
Acts as the execution router, connecting parsed intents to their corresponding domain handlers.

#### Logic Walkthrough:
- **`Response` Dataclass (Lines 15-20)**:
  Standardized execution result:
  - `success`: boolean indicating if the handler completed successfully.
  - `message`: user-facing Rich string to print or speak.
  - `data`: optional dict/dataclass carrying structured records (crucial for conversation memory reference resolution).
- **`DecisionEngine.register(self, intent_type, handler, service_key)` (Lines 30-35)**:
  Maps an `IntentType` directly to a handler function (e.g., `handle_add_task` in `handlers.py`) and registers the service dependency (e.g. `"tasks"`).
- **`DecisionEngine.process(self, intent: Intent) -> Response` (Lines 40-60)**:
  1. Validates if a handler exists for `intent.intent`.
  2. Resolves handler parameters using `self.context`.
  3. Calls the handler inside a try-catch block:
     ```python
     response = handler(intent, self.context)
     ```
  4. Returns the standardized `Response`.

---

### 3. `jarvis/core/memory.py`
Provides conversational memory and Ordinal/Pronoun Reference Resolution ("the first one done").

#### Logic Walkthrough:
- **`ConversationTurn` Class (Lines 10-18)**:
  Represents one exchange. Stores `role` ("user"/"assistant"), `text`, `timestamp`, and optional `intent` and `response_data` (carrying the exact objects listed, like task IDs).
- **`SessionMemory` Class (Lines 22-50)**:
  Maintains a list of `ConversationTurn` history. Capped at **20 turns** via a sliding window slicing (`self.conversation_history = self.conversation_history[-20:]`).
- **`MemoryEngine.resolve_reference(self, text: str) -> str` (Lines 55-90)**:
  Implements ordinal matching (e.g. `"first one"`, `"second one"`, `"last one"`, `"that one"`):
  1. Scans `text` using regular expressions for references: `r"(first|second|third|last)\s+(one|task|goal|habit)"`.
  2. If found, it fetches the *last assistant turn* from history:
     ```python
     last_turn = self.session.get_last_assistant_turn()
     ```
  3. Extracts the cached objects from `last_turn.response_data` (e.g., a listed array of tasks).
  4. Maps the matched ordinal to the array index:
     - `"first"` $\rightarrow$ `index 0`
     - `"second"` $\rightarrow$ `index 1`
     - `"last"` $\rightarrow$ `index -1`
  5. Replaces the ordinal placeholder in the user's raw input string with the actual database ID of the target object:
     - User says: `"delete the first one"` $\rightarrow$ Resolved to: `"delete task 8caf9fae"`.
  6. Returns the updated, fully qualified query string.

---

## 🛠️ Domain Skills & Algorithms (`jarvis/skills/`)

### 1. `jarvis/skills/daily_tasks.py`
Determines which tasks out of the entire database should be completed today using an energy-aware heuristic.

#### Logic Walkthrough:
- **`DailyTaskService.generate_daily(self, date_obj, limit)` (Lines 30-70)**:
  1. Queries SQLite for all tasks with status `'pending'`:
     ```sql
     SELECT * FROM tasks WHERE status = 'pending'
     ```
  2. Scores every pending task using the **Selection Priority Score Formula**:
     - **Base score** is initialized to the task's manual priority field (`1` to `5`).
     - If the task has a deadline:
       - If the deadline has already passed (overdue), it adds an **overdue penalty**: `overdue_days * 3.0`.
       - If the deadline is within the next 7 days, it adds an **urgency boost**: `(7 - days_until) / 7 * 2.0`.
  3. Evaluates sequential task locks: If a task belongs to a hierarchical goal and has a designated preceding milestone, it check if that milestone is completed. If not completed, the task score is temporarily set to `0` to enforce order.
  4. Sorts tasks by descending score and selects the top `limit` (default: 5) tasks.
  5. Inserts the selected tasks into the `daily_tasks` table for tracking completion status.

---

### 2. `jarvis/skills/schedule.py`
Dynamically schedules tasks into hourly blocks matching the user's daily energy patterns.

#### Logic Walkthrough:
- **`ScheduleEngine.generate_schedule(...)` (Lines 186-271)**:
  1. Inspects the current time of day (`get_time_of_day()`) to calculate the user's **Available Energy**:
     - Morning (6:00-12:00) energy ceiling: `8` (high-cognitive focus block).
     - Afternoon (12:00-17:00) energy ceiling: `5` (routine tasks focus).
     - Evening (17:00-22:00) energy ceiling: `4` (lighter tasks/wind down).
     - Night (22:00-6:00) energy ceiling: `2`.
  2. Matches the task's manual `energy_level` (1-10) against Available Energy:
     - `Energy Fit = AbsoluteDifference(TaskEnergy - AvailableEnergy)`.
     - Fits within a difference of $\le 2$ score `1.0` (Perfect Fit).
     - Fits within a difference of $\le 4$ score `0.6`.
     - Otherwise, fits score `0.1` (Poor Fit).
  3. Schedules tasks into consecutive hourly blocks starting at `work_start` (default: 9:00 AM).
  4. Automatically injects a short **5-minute break slot** (`type="break"`) immediately following each completed task block to manage burnout.
  5. Evaluates scheduled cognitive loads and adds warning flags if more than 3 consecutive high-energy tasks are placed back-to-back.

---

### 3. `jarvis/skills/briefing.py`
Generates the daily morning briefings, detailing tasks due, energy recommendations, and recommended schedules.

#### Logic Walkthrough:
- **`BriefingService.generate(self, user_name)` (Lines 16-37)**:
  1. Builds greeting strings dynamically based on local server hour (`_get_greeting()`).
  2. Appends formatted local date info.
  3. Queries today's assigned tasks (`_get_task_summary()`) from the `daily_tasks` table.
  4. Lists any manually set hard-deadline tasks due today.
  5. Invokes the schedule generator (`_get_schedule_suggestion()`) to calculate hourly blocks.
  6. **Phase 0 Output Fix (Lines 172-181)**:
     Loops over all `schedule.slots` and prints the concrete hourly intervals:
     ```python
     for slot in schedule.slots:
         time_str = f"{slot.start.strftime('%H:%M')} - {slot.end.strftime('%H:%M')}"
         if slot.type == "break":
             lines.append(f"      • {time_str} [Break]")
         else:
             energy_tag = "[High]" if slot.energy_level and slot.energy_level >= 7 else "[Low]"
             lines.append(f"      • {time_str} {energy_tag} {slot.task_title}")
     ```
     This prevents the schedule details from cutting off and provides a complete summary of scheduled events.

---

## 🔊 Audio & Voice Pipeline (`jarvis/voice/`)

### 1. `jarvis/voice/audio.py`
Captures low-level audio stream buffers and suppresses operating system ALSA warning noises.

#### Logic Walkthrough:
- **ALSA Silence C-Level Suppressor (Lines 12-23)**:
  1. Loads standard C audio library `libasound.so.2` using Python `ctypes`:
     ```python
     asound = cdll.LoadLibrary('libasound.so.2')
     ```
  2. Declares a custom ctypes callback type matching the ALSA error function signature:
     ```python
     ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
     ```
  3. Binds standard ALSA error redirection to a dummy Python method (`py_error_handler` which does absolutely nothing):
     ```python
     asound.snd_lib_error_set_handler(c_error_handler)
     ```
  4. Completely silences hundreds of ALSA console spam lines on PyAudio stream initialization.
- **`AudioCapture.record_until_silence(...)` (Lines 144-189)**:
  1. Starts an audio input stream (`pyaudio.paInt16`, `16000Hz` sample rate).
  2. Loops and reads chunk buffers (`AudioConfig.chunk_size = 1024` frames).
  3. Calculates the root mean square (RMS) amplitude of each chunk:
     ```python
     mean_amplitude = np.abs(audio).mean()
     ```
  4. If `mean_amplitude` falls below `silence_threshold` (default: 500) for more than `silence_timeout` (default: 2s) *after* speech has already started, it stops recording.
  5. Converts raw bytes into normalized `float32` numpy arrays and closes the stream.

---

### 2. `jarvis/voice/voice_cli.py`
The always-listening voice command loop and background habits reminder daemon.

#### Logic Walkthrough:
- **`VoiceInterface.start(self)` (Lines 111-183)**:
  1. Runs checks on audio/STT/TTS dependencies.
  2. Spawns the background scheduler thread:
     ```python
     threading.Thread(target=self._reminder_loop, daemon=True).start()
     ```
  3. Starts wake-word detection using openWakeWord/Simple engines.
  4. When wake-word is triggered, calls `_on_wake_word`, stops the low-power listener, plays a beep sound, listens to the user command via `record_until_silence()`, runs NLU routing, and speaks the result back via Piper TTS.
- **`VoiceInterface._reminder_loop(self)` (Lines 185-201)**:
  1. Runs as a background daemon loop, sleeping for 10 seconds per iteration.
  2. On every new minute, invokes `_check_and_trigger_reminders(now)`.
- **`VoiceInterface._check_and_trigger_reminders(self, now)` (Lines 203-242)**:
  1. Uses the unified `get_services()` singleton to fetch database entities.
  2. Compares active habit `reminder_time` values (e.g. `"18:30"`) with `now.strftime("%H:%M")`.
  3. Queries the `habit_logs` table for habit completions logged today.
  4. If a habit matches the current time and has *not* been completed today:
     - Dispatches a Piper text synthesis request in a background thread so it doesn't block wake-word listening:
       ```python
       threading.Thread(target=self.speak, args=(message,), daemon=True).start()
       ```
     - Logs the reminder timestamp to the SQLite `accountability_log` database.

---

## 🌐 FastAPI REST Layer (`jarvis/dashboard/backend/`)

### 1. `jarvis/dashboard/backend/main.py`
Exposes system endpoints to the React front-end and mounts Vite SPA index paths.

#### Logic Walkthrough:
- **FastAPI Core Middleware Setup (Lines 26-43)**:
  Ensures CORS allows credentials matching Vite:
  ```python
  origins = [
      "http://localhost:3000",
      "http://localhost:5173",
      "http://127.0.0.1:3000",
      "http://127.0.0.1:5173",
  ]
  # Merges custom config.api.cors_origins dynamically to avoid hardcoding.
  ```
- **`GET /api/profile` (Lines 52-80)**:
  Queries `UserProfile` via `ProfileService`, checks the `grad_deadline` date, computes days remaining using `(grad_deadline - date.today()).days`, and checks if today is Saturday/Sunday/Monday to return a boolean `is_grad_day`.
- **`GET /api/dashboard` (Lines 266-286)**:
  Asynchronously executes multiple parallel skill checks:
  ```python
  profile_data = await get_profile()
  habits_data = await get_habits()
  weekly_data = await get_weekly_stats()
  ```
  Returns a combined JSON carrying days remaining, today's day name, active habits completed/total ratio, random motivational quote, and habit completion percentage for frontend rendering.
