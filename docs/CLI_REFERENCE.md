# CLI Reference Documentation

Complete command-line interface reference for JARVIS - Your Local AI Assistant.

---

## Quick Start

```bash
# Navigate to JARVIS directory
cd /path/to/JARVIS

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Run JARVIS
python -m jarvis.cli --help
```

---

## All Commands Overview

```
jarvis accountability  - Accountability and motivation
jarvis ask             - Natural language queries
jarvis briefing        - Daily briefing
jarvis goal            - Goal management
jarvis habit           - Habit tracking
jarvis know            - Knowledge base
jarvis note            - Notes
jarvis profile         - User profile
jarvis review          - Daily/weekly reviews
jarvis schedule        - Energy-aware scheduling
jarvis setup-life      - Initial life management setup
jarvis shell           - Interactive shell mode
jarvis status          - Overall status
jarvis task            - Task management
jarvis university      - University LMS integration
jarvis voice           - Voice interface
```

---

## Accountability Commands

Daily accountability to keep you on track.

### Today's Focus
```bash
jarvis accountability today
```
Shows:
- Today's date and day of week
- Grad project day (if Sat/Sun/Mon)
- Your pending habits
- Upcoming deadlines

### Graduation Countdown
```bash
jarvis accountability countdown
```
Shows days remaining until graduation (June 1, 2026).

### Motivational Push
```bash
jarvis accountability push
```
Get a motivational message to keep you going.

### Overdue Items
```bash
jarvis accountability overdue
```
Shows any missed goals or overdue tasks.

---

## Goal Commands

Hierarchical goals with milestones and progress tracking.

### List Goals
```bash
jarvis goal list
jarvis goal list --area career
```

### View Goal
```bash
jarvis goal view <goal_id>
```
Shows goal details and all milestones.

### Add Goal
```bash
jarvis goal add "Goal Title" --area career --deadline 2026-06-01 --priority high
```

**Options:**
- `--area` - Life area: career, projects, learning, religion, health, finance, personal
- `--deadline` - Target date (YYYY-MM-DD)
- `--priority` - low, medium, high, critical

### Update Progress
```bash
jarvis goal progress <goal_id> 50
```
Update goal progress (0-100%).

---

## Habit Commands

Daily habit tracking with streaks.

### List Habits
```bash
jarvis habit list
```
Shows all habits with:
- ID
- Name
- Life area
- Current streak
- Today's status (Done/Pending)

### Log Habit
```bash
jarvis habit log <habit_id> --pages 2 --duration 30
```

**Options:**
- `--pages N` - Pages completed (for Quran)
- `--duration N` - Duration in minutes

### Quick Check
```bash
jarvis habit check <habit_id>
```
Mark habit as complete for today (no extra details).

### View Stats
```bash
jarvis habit stats
jarvis habit stats <habit_id>
```
Shows:
- Current streak
- Best streak
- Total completions
- Last 30 days completion rate

### Add Habit
```bash
jarvis habit add "Habit Name" --frequency daily --time evening --area career
```

**Options:**
- `--frequency` - daily, weekly
- `--time` - morning, evening
- `--area` - Life area ID
- `--duration` - Duration in minutes

---

## Profile Commands

Your personal profile and preferences.

### View Profile
```bash
jarvis profile list
```
Shows:
- Name
- Work style
- Grad deadline
- Job preference
- Accountability style

### Set Value
```bash
jarvis profile set <key> <value>
```

---

## Review Commands

Daily and weekly reviews.

### Daily Review
```bash
jarvis review daily --mood 8 --energy 7 --productivity 8
```

**Options:**
- `--mood N` - Mood 1-10
- `--energy N` - Energy level 1-10
- `--productivity N` - Productivity 1-10
- `--notes TEXT` - Notes

### Weekly Review
```bash
jarvis review weekly
```
Shows weekly summary with habit completion rate.

---

## Task Commands

One-off tasks and todo items.

### Add Task
```bash
jarvis task add "Task title" --priority 5 --energy 7
```

### List Tasks
```bash
jarvis task list
jarvis task list --status pending
jarvis task list --status completed
```

### Complete Task
```bash
jarvis task complete <task_id>
```

### Delete Task
```bash
jarvis task delete <task_id>
```

### View Task
```bash
jarvis task view <task_id>
```

---

## Note Commands

Quick notes and documentation.

### Add Note
```bash
jarvis note add "Note title" --content "Note content"
```

### List Notes
```bash
jarvis note list
```

### Search Notes
```bash
jarvis note search "keyword"
```

### View Note
```bash
jarvis note view <note_id>
```

---

## Knowledge Commands

Facts and information storage.

### Add Knowledge
```bash
jarvis know add "Important fact"
jarvis know add "Python tip" --category coding
```

### List Knowledge
```bash
jarvis know list
jarvis know list --category coding
```

### Search Knowledge
```bash
jarvis know search "python"
```

---

## Schedule Commands

Energy-aware scheduling.

### Generate Schedule
```bash
jarvis schedule
jarvis schedule --date 2026-04-15
```

### Daily Briefing
```bash
jarvis briefing
```

---

## Voice Commands

Voice interface for hands-free interaction.

### Test Voice Setup
```bash
jarvis voice --test
```
Tests:
- Audio input devices
- Speech recognition (Whisper)
- Text-to-speech (Piper)

### Push-to-Talk
```bash
jarvis voice --ptt
```
Press Enter, speak, press Enter again. JARVIS listens and responds.

### Continuous Listening
```bash
jarvis voice --continuous
```
Always listening. Say "exit" to quit.

### Wake Word Mode
```bash
jarvis voice
```
Says "Hey JARVIS" to activate. Uses simple keyword detection.

---

## University Commands

Moodle LMS integration.

### Setup
```bash
jarvis university setup --url https://moodle.youruni.edu --username your_user
# Prompts for password
```

### Sync
```bash
jarvis university sync
```

### View Courses
```bash
jarvis university courses
```

### View Tasks
```bash
jarvis university tasks
```

### Status
```bash
jarvis university status
```

---

## Other Commands

### Natural Language
```bash
jarvis ask "what tasks are due this week"
jarvis ask "add a task to call mom"
jarvis ask "show my schedule for today"
```

### Interactive Shell
```bash
jarvis shell
```
Opens interactive conversation mode.

### Status
```bash
jarvis status
```

### Initial Setup
```bash
jarvis setup-life
```
Sets up life management with your profile and goals.

---

## Life Areas

| ID | Area | Description |
|----|------|-------------|
| career | Career | Job, UE5, grad project, portfolio |
| projects | Projects | LINKIT, Legendary Mansaf, Afterfall |
| learning | Learning | Python, English, French/German, IT |
| religion | Religion | Quran, Prayer, Islamic knowledge |
| health | Health | Exercise, sleep, diet |
| finance | Finance | Budget, savings |
| personal | Personal | Relationships, hobbies |

---

## Your Current Setup

**Profile:**
- Name: Deep
- Work Style: Evening
- Grad Deadline: June 1, 2026
- Graduation: July 2026
- Job Preference: Hybrid

**Habits:**
| Habit | ID |
|-------|-----|
| Quran Recitation | 399d5464 |
| Prayer (5x Daily) | bd3e9056 |
| UE5 Practice | 074498b6 |
| LINKIT Development | fe8ffc4d |
| Python Practice | 900c8682 |
| English Study | 996e0789 |
| Grad Project Work | 0dd2c8cf |

**Weekly Schedule:**
- Sat/Sun/Mon: Grad project (morning), evening tasks
- Tue/Wed/Thu: Full evening blocks for LINKIT, UE5, Python
- Friday: Light tasks, week review

---

## Installation

### Direct
```bash
cd JARVIS
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m jarvis.main
jarvis setup-life
```

### Docker
```bash
./run.sh build
./run.sh start
./run.sh shell
```

---

<div align="center">

**Type `python -m jarvis.cli --help` anytime for quick reference.**

</div>
