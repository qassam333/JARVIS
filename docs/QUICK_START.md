# JARVIS - Quick Start Guide

> **Get your local AI assistant running in 5 minutes.**

---

## Prerequisites

- Python 3.11 or higher
- 8GB+ RAM (16GB recommended)
- Linux/macOS/Windows with WSL

---

## Installation

### 1. Clone or Navigate to Project

```bash
cd JARVIS
```

### 2. Install Dependencies

Using Poetry (recommended):

```bash
# Install Poetry if not installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

Or using pip:

```bash
pip install -e .
```

### 3. Initialize Database

```bash
jarvis init
# Creates ./data/jarvis.db with all tables
```

### 4. Configure (Optional)

```bash
# Set your name
jarvis config set user.name "Your Name"

# Set data directory (optional)
jarvis config set jarvis.data_dir "/path/to/data"
```

---

## Basic Usage

### Tasks

```bash
# Add a task
jarvis task add "Study Python" --energy 7 --deadline tomorrow

# List tasks
jarvis task list

# Complete a task
jarvis task done <task_id>

# View tasks due today
jarvis task list --date today
```

### Notes

```bash
# Add a note
jarvis note add "Meeting Notes" --content "Discussed Q1 goals"

# Search notes
jarvis note search "meeting"

# List notes by tag
jarvis note list --tag work
```

### Knowledge

```bash
# Store a fact
jarvis know add "Python uses whitespace for blocks" --category coding

# Search knowledge
jarvis know search python
```

### Schedule

```bash
# Generate daily schedule
jarvis schedule generate

# Show schedule
jarvis schedule show

# Get morning briefing
jarvis briefing
```

---

## University Integration (Optional)

### Setup Moodle Connection

```bash
# Start setup
jarvis university setup --moodle https://your-lms.edu

# Enter your credentials when prompted
Username: youruni_username
Password: ************

# Manual sync
jarvis university sync

# View imported assignments
jarvis university tasks
```

---

## Voice Interface (Optional)

### Install Voice Dependencies

```bash
# Install PyAudio for microphone access
pip install pyaudio

# Download Whisper model (base)
python -c "import whisper; whisper.load_model('base')"

# Download Piper TTS
# See docs/VOICE_INTERFACE.md for installation
```

### Enable Voice

```bash
# Edit config.yaml
vim config.yaml

# Set:
# voice:
#   enabled: true

# Start voice mode
jarvis voice
```

Say **"Hey JARVIS"** to activate, then speak your command.

---

## Common Workflows

### Morning Routine

```bash
# Get your daily briefing
jarvis briefing

# Shows:
# - Energy level
# - Tasks due today
# - University assignments
# - Weather (if configured)
```

### Adding University Task

```bash
# Sync from university
jarvis university sync

# All assignments auto-imported as tasks
jarvis task list --source moodle
```

### Evening Review

```bash
# View what you accomplished
jarvis task list --status completed --date today

# Add tomorrow's tasks
jarvis task add "Plan tomorrow" --energy 3
jarvis task add "Read chapter 5" --energy 5 --deadline tomorrow
```

---

## Directory Structure

```
JARVIS/
├── jarvis/              # Main package
│   ├── core/           # Brain & decision engine
│   ├── db/             # Database layer
│   ├── skills/         # Task, note, knowledge skills
│   └── voice/          # Voice interface
├── data/               # SQLite database (created on init)
├── config.yaml         # Configuration
├── pyproject.toml      # Dependencies
└── docs/               # Full documentation
```

---

## Troubleshooting

### "jarvis: command not found"

```bash
# Install in development mode
pip install -e .

# Or use poetry
poetry run jarvis --help
```

### Database errors

```bash
# Reinitialize database
rm data/jarvis.db
jarvis init
```

### Voice not working

```bash
# Check microphone
arecord -l  # Linux
# or
# System Preferences > Sound (macOS)

# Test audio
python -c "import pyaudio; p = pyaudio.PyAudio(); print(p.get_device_count())"
```

---

## Getting Help

```bash
# Main help
jarvis --help

# Command help
jarvis <command> --help

# View documentation
cat docs/ARCHITECTURE.md
cat docs/CLI_REFERENCE.md
```

---

## Next Steps

1. **Customize config.yaml** - Set your preferences
2. **Set up university** - Automate assignment tracking
3. **Enable voice** - Hands-free interaction
4. **Read docs/** - Full technical documentation

---

<div align="center">

**Welcome to your local AI assistant.**

**Privacy-first. Deterministic. Yours.**

</div>
