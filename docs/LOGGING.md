# Logging System Documentation

> **Purpose**: Structured logging for debugging, auditing, and monitoring.

---

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LOGGING SYSTEM                           │
│                                                              │
│  ┌──────────────┐                                           │
│  │ Application │                                           │
│  └──────┬──────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Structured Logger                        │   │
│  │                                                         │   │
│  │  Levels: DEBUG | INFO | WARNING | ERROR | CRITICAL    │   │
│  │  Outputs: Console | File | Syslog                     │   │
│  │  Format: JSON (file) | Pretty (console)              │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ├────────────────┬────────────────┐                  │
│         ▼                ▼                ▼                  │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐         │
│  │  Console   │   │  Log File  │   │  Syslog    │         │
│  │  (pretty) │   │  (json)    │   │  (server)  │         │
│  └────────────┘   └────────────┘   └────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| **DEBUG** | Detailed debugging info | "Entering function X", variable values |
| **INFO** | General events | "Task created", "Sync completed" |
| **WARNING** | Unexpected but handled | "Retry attempt 2/3", "Config missing" |
| **ERROR** | Errors that need attention | "Database write failed", "Auth error" |
| **CRITICAL** | System failure | "Database corruption", "Out of disk" |

---

## What We Log

### ✅ DO Log

```python
logger.info("Task created", extra={"task_id": "abc-123", "title": "Study"})
logger.warning("Retry attempt", extra={"attempt": 2, "max_retries": 3})
logger.error("Database write failed", extra={"error": str(e), "table": "tasks"})
```

### ❌ NEVER Log

```python
# Passwords, tokens, API keys
logger.debug(f"Password: {password}")           # NEVER
logger.info(f"Token: {session_token}")        # NEVER

# Sensitive user data
logger.debug(f"User data: {user_data}")        # NEVER

# Full request bodies with credentials
logger.debug(f"Request: {request_body}")       # BE CAREFUL
```

---

## Log Format

### Console (Human-readable)

```
2024-01-15 10:30:45 [INFO] Task created: abc-123
2024-01-15 10:30:46 [WARNING] Retry attempt 2/3: network timeout
2024-01-15 10:30:47 [ERROR] Database write failed: constraint violation
```

### File (JSON - for parsing)

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "Task created",
  "task_id": "abc-123",
  "source": "jarvis.skills.tasks"
}
```

---

## Implementation

### Logger Configuration

```python
# jarvis/utils/logger.py

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for file output"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "source": record.name,
        }
        
        # Add extra fields
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class SensitiveFilter(logging.Filter):
    """Filter out sensitive data"""
    
    SENSITIVE_PATTERNS = [
        "password", "token", "secret", "api_key", 
        "credential", "auth", "private"
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                record.msg = "[SENSITIVE DATA REDACTED]"
                return True
        return True


def setup_logger(
    name: str = "jarvis",
    level: str = "INFO",
    log_dir: Path = None,
    debug: bool = False
) -> logging.Logger:
    """Setup and return logger"""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.addFilter(SensitiveFilter())
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler (pretty)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(console)
    
    # File handler (JSON)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_dir / "jarvis.log",
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    # Debug mode adds more verbose console output
    if debug:
        console.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    return logger
```

---

## Usage Examples

### Basic Usage

```python
from jarvis.utils.logger import setup_logger

logger = setup_logger(debug=True)

# Log events
logger.info("JARVIS started")
logger.info("Task created", extra={"task_id": "abc-123"})
logger.warning("Config file not found, using defaults")
logger.error("Failed to connect to database")
```

### In Skills

```python
# jarvis/skills/tasks.py

import logging

logger = logging.getLogger("jarvis.skills.tasks")

class TasksSkill:
    
    def add_task(self, title: str, **kwargs):
        logger.info("Creating task", extra={"title": title})
        
        try:
            task = self._create_task(title, **kwargs)
            logger.info("Task created", extra={"task_id": task.id})
            return task
            
        except Exception as e:
            logger.error("Failed to create task", extra={
                "error": str(e),
                "title": title
            })
            raise
```

### In University Scraper

```python
# jarvis/skills/university/sync.py

logger = logging.getLogger("jarvis.university")

class SyncManager:
    
    def sync(self):
        logger.info("Starting university sync", extra={
            "service": "moodle"
        })
        
        try:
            # ... sync logic
            
            logger.info("Sync completed", extra={
                "items_fetched": 15,
                "tasks_created": 3,
                "duration_seconds": 45.2
            })
            
        except Exception as e:
            logger.error("Sync failed", extra={
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
```

---

## Log File Structure

```
data/
└── logs/
    ├── jarvis.log              # Current log (rotated)
    ├── jarvis.log.1           # Previous
    ├── jarvis.log.2           # Older
    └── ...
```

---

## CLI Integration

```bash
# View recent logs
jarvis logs

# View last 50 lines
jarvis logs --lines 50

# Follow logs in real-time
jarvis logs --follow

# View only errors
jarvis logs --level error

# Export logs
jarvis logs --export logs.zip
```

---

## Log Retention

| Log Type | Retention | Reason |
|----------|-----------|--------|
| Console | None | Not stored |
| File (JSON) | 7 days | Rotated, 5 files max |
| Audit | 30 days | Security compliance |

---

## Security Considerations

1. **No credentials** - SensitiveFilter blocks password/token logging
2. **No PII** - Filter personal data from logs
3. **Encrypted logs** (future) - Encrypt log files at rest
4. **Access control** - Only user can read logs

---

## Troubleshooting with Logs

```bash
# Find all errors
jarvis logs --level error

# Find task-related logs
jarvis logs | grep task

# Find sync issues
jarvis logs --service university | grep -i error

# Debug specific operation
jarvis --debug task add "test"
# Shows detailed logs
```

---

<div align="center">

**Logs: Debug today, understand forever.**

</div>
