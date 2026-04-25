# JARVIS - Your Local AI Assistant

Think of JARVIS as your personal digital assistant that lives entirely on your computer. No cloud, no subscriptions, no data leaving your machine. It manages your life goals, tracks habits, reminds you of what matters, and helps you stay accountable to yourself.

This started as a project to build a privacy-focused second brain. It grew into a complete life management system.

## What JARVIS Does

- **Goal Management** - Hierarchical goals with milestones and progress tracking
- **Habit Tracking** - Daily habits with streaks and accountability
- **Smart Scheduling** - Plans your day based on your energy and priorities
- **Personal Profile** - Learns your work style, preferences, and patterns
- **Accountability** - Strict but motivational reminders to keep you on track
- **Note Taking** - Quick notes with search and organization
- **Knowledge Base** - Store facts and information you want to remember
- **University Integration** - Syncs with Moodle to import courses and assignments
- **Voice Interface** - Talk to JARVIS instead of typing (optional)

Everything runs locally. Your data never leaves your computer.

## Requirements

- Python 3.11 or higher
- 4GB RAM minimum (8GB recommended)
- For voice: microphone and speakers
- Docker (optional, for containerized setup)

## Quick Start

### Option 1: Direct Installation

```bash
# Clone or navigate to the project
cd JARVIS

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with all features
pip install -e ".[all]"

# Initialize the database with migrations
python -m jarvis.main

# Run the life management setup
jarvis setup-life

# Run JARVIS
jarvis --help
```

### Option 2: Docker

```bash
# Build the container
./run.sh build

# Start the CLI
./run.sh start

# Open a shell in the container
./run.sh shell
```

## First Steps

After installation, try these commands:

```bash
# See your accountability for today
jarvis accountability today

# List your goals
jarvis goal list

# List your habits
jarvis habit list

# Check graduation countdown
jarvis accountability countdown

# Get a motivational push
jarvis accountability push

# Log a habit (Quran with pages)
jarvis habit log 399d5464 --pages 2

# Quick habit check
jarvis habit check 074498b6
```

## Life Management System

JARVIS includes a complete life management system built around your goals.

### Your Profile

Your profile stores your personal information and preferences:

```bash
# View your profile
jarvis profile list

# Set profile values
jarvis profile set work_days "sat,sun,mon"
```

Current settings:
- Work style: Evening (18:00-22:00 blocks)
- Grad project days: Saturday, Sunday, Monday (3-5hr sessions)
- Job preference: Hybrid
- Graduation deadline: June 1, 2026

### Goals

Goals are hierarchical with milestones. Track progress from 0-100%.

```bash
# List all goals
jarvis goal list

# View goal details with milestones
jarvis goal view <goal-id>

# Update progress
jarvis goal progress <goal-id> 50

# Add a new goal
jarvis goal add "Learn Blender" --area projects --priority high

# Areas: career, projects, learning, religion, health, finance, personal
```

### Habits

Daily habits with streak tracking. Log completion with optional data (pages for Quran, duration, etc).

```bash
# List all habits
jarvis habit list

# Log completion with details
jarvis habit log <habit-id> --pages 2 --duration 30

# Quick check (no details)
jarvis habit check <habit-id>

# View statistics
jarvis habit stats <habit-id>

# All habits stats
jarvis habit stats

# Add new habit
jarvis habit add "Evening Reading" --frequency daily --time evening
```

### Daily Review

End your day with a quick review:

```bash
jarvis review daily --mood 8 --energy 7 --productivity 8
```

### Weekly Review

See your week's progress:

```bash
jarvis review weekly
```

### Accountability

The accountability system keeps you on track with strict but motivational messages:

```bash
# What's due today
jarvis accountability today

# Graduation countdown
jarvis accountability countdown

# Get motivated
jarvis accountability push

# Check overdue items
jarvis accountability overdue
```

### Your Schedule

JARVIS schedules based on your evening productivity blocks:

- **Saturday, Sunday, Monday**: Grad project (morning), lighter evening tasks
- **Tuesday, Wednesday, Thursday**: Full evening blocks for LINKIT, UE5, Python
- **Friday**: Light tasks, week review

Priority order for evenings:
1. LINKIT Development (most urgent)
2. UE5 Practice
3. Python Practice
4. English Study

## Goal-to-Tasks System

JARVIS can break down goals into actionable tasks automatically:

```bash
# Add a new goal
jarvis goal add "Build Portfolio" --area career --deadline 2026-12-01 --priority high

# Generate tasks from the goal
jarvis goal tasks generate <goal-id>

# Or generate tasks for ALL goals
jarvis goal tasks generate --all

# List tasks for a specific goal
jarvis goal tasks list <goal-id>
```

The generator creates phase-based tasks with deadlines:
- **Career goals** → Graduation, UE5, Job Search, Portfolio specific phases
- **Project goals** → LINKIT, Mansaf, Afterfall specific phases
- **Learning goals** → Python, English, Third Language specific phases

Each task is linked to the goal via `goal_id` for tracking.

## Daily Task Selection

JARVIS selects the best tasks for each day based on:

1. **Priority Score** = Base priority + Deadline urgency + Overdue penalty
2. **Sequential Order** - Next task unlocks only when previous is done
3. **Goal Diversity** - Mix of different goals per day

```bash
# Generate today's task list (auto-selects top 5)
jarvis daily generate

# Generate with custom limit
jarvis daily generate --limit 3

# List today's tasks
jarvis daily list

# Mark task as done
jarvis daily complete <task-id>

# Roll over undone tasks to tomorrow
jarvis daily reroll

# View history
jarvis daily history
```

### Priority Scoring Algorithm

```
score = base_priority

if deadline passed:
    score += overdue_days * 3 (overdue penalty)
else if deadline within 7 days:
    score += (7 - days_until) / 7 * 2 (urgency boost)
```

### Daily Workflow

```bash
# Morning: Generate today's tasks
jarvis daily generate

# Check what's due
jarvis daily list

# Also shows in briefing
jarvis briefing

# Complete tasks as you go
jarvis daily complete <task-id>

# End of day: Roll over undone
jarvis daily reroll
```

## Command Reference

### Task Management

```bash
jarvis task add "Task name" --priority 5 --energy 7
jarvis task list
jarvis task complete <task-id>
```

### Notes

```bash
jarvis note add "Meeting notes" --content "..."
jarvis note list
jarvis note search "keyword"
```

### Knowledge

```bash
jarvis know add "Important fact"
jarvis know list
jarvis know search "fact"
```

### Natural Language

```bash
jarvis ask "what tasks are due this week"
jarvis ask "add a task to call mom tomorrow"
```

### Interactive Shell

```bash
jarvis shell
```

### Daily Briefing

```bash
jarvis briefing
jarvis schedule
```

## University Integration

Connect to your Moodle LMS:

```bash
# Setup
jarvis university setup --url https://moodle.youruni.edu --username your_user

# Sync
jarvis university sync

# View data
jarvis university courses
jarvis university tasks
```

## Voice Interface (Optional)

Voice requires additional setup:

```bash
# Install voice dependencies
pip install pyaudio sounddevice scipy openai-whisper

# Download Piper TTS from https://github.com/rhasspy/piper

# Run in different modes
jarvis voice              # Wake word mode
jarvis voice --ptt       # Push-to-talk
jarvis voice --continuous # Always listening
jarvis voice --test      # Test setup
```

## Configuration

Edit `config.yaml`:

```yaml
jarvis:
  name: "JARVIS"
  data_dir: "./data"

voice:
  enabled: true
  wake_word: "hey jarvis"
  stt_model: "base"

privacy:
  encrypted: true
  telemetry: false
```

Or use environment variables:

```bash
export JARVIS_DATA_DIR=/path/to/data
export JARVIS_LOG_LEVEL=debug
```

## Auto-Start with System

Make JARVIS start automatically when your PC boots:

```bash
cd JARVIS/autostart
./install.sh install
```

Options:
- `./install.sh systemd` - Systemd service (recommended for Linux)
- `./install.sh desktop` - Desktop autostart entry
- `./install.sh uninstall` - Remove autostart

On startup, JARVIS will show your daily accountability and countdown.

## Docker Commands

```bash
./run.sh build      # Build the Docker image
./run.sh start      # Start JARVIS container
./run.sh stop       # Stop the container
./run.sh restart    # Restart the container
./run.sh logs       # View logs (add -f to follow)
./run.sh shell      # Open shell in container
./run.sh status     # Show container status
./run.sh api        # Start with REST API (port 8000)
./run.sh clean      # Remove containers and images
```

## REST API

Start the web API:

```bash
jarvis api
# Or with Docker: ./run.sh api
# Then visit http://localhost:8000
```

## Data Location

- Database: `./data/jarvis.db`
- Logs: `./data/`

For Docker, these are mounted volumes so data persists.

## Troubleshooting

### Database Issues

```bash
# Reset database (loses all data)
rm data/jarvis.db
python -m jarvis.main
jarvis setup-life
```

### Voice Not Working

1. Run `jarvis voice --test`
2. Check microphone is connected
3. Verify Whisper and Piper are installed

### Docker Issues

```bash
./run.sh clean
./run.sh build
./run.sh start
```

## Privacy

JARVIS is designed with privacy as a core principle:

- All data stays on your machine
- No cloud services or external APIs required
- No telemetry or analytics
- Credentials are encrypted in the database
- You own your data completely

## Project Structure

```
JARVIS/
├── jarvis/
│   ├── core/          # Intent parsing, decision engine, memory
│   ├── db/            # Database layer and migrations
│   ├── skills/        # All services
│   │   ├── goals.py       # Goal management
│   │   ├── habits.py      # Habit tracking
│   │   ├── reviews.py     # Daily/weekly reviews
│   │   ├── profile.py     # User profile
│   │   └── accountability.py  # Motivation engine
│   ├── voice/         # Speech recognition and synthesis
│   ├── api/           # REST API endpoints
│   └── utils/         # Configuration, logging
├── data/              # Database and persistent storage
├── docs/              # Detailed documentation
├── config.yaml        # Configuration file
└── run.sh             # Docker management script
```

## License

This project is for personal use. You're free to modify and extend it as needed.

---

Built for privacy. Built to work. Built to keep you accountable.
