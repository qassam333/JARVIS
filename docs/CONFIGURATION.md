# Configuration System Documentation

> **Purpose**: Flexible configuration with file, environment variables, and defaults.

---

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 CONFIGURATION SYSTEM                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Configuration Sources                │   │
│  │                                                        │   │
│  │   ┌─────────────┐    ┌─────────────┐                │   │
│  │   │  config.yaml │ + │ Environment │ + Defaults    │   │
│  │   │  (file)      │    │ Variables   │                │   │
│  │   └─────────────┘    └─────────────┘                │   │
│  │          │                  │                        │   │
│  │          └──────────────────┼─────────────────────── │   │
│  │                             │                        │   │
│  │                             ▼                        │   │
│  │   ┌──────────────────────────────────────────────┐   │   │
│  │   │            Merged Configuration               │   │   │
│  │   │                                                │   │   │
│  │   │  Priority: ENV > config.yaml > defaults        │   │   │
│  │   └──────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration Files

### 1. config.yaml (Versioned in repo)

```yaml
jarvis:
  name: "JARVIS"
  version: "0.1.0"
  data_dir: "./data"
  database: "jarvis.db"
  debug: false

user:
  name: null
  timezone: "UTC"
  preferences: {}

university:
  enabled: false
  auto_sync: false
  sync_time: "06:00"
  services: []

voice:
  enabled: false
  wake_word: "hey jarvis"
  stt_model: "base"
  tts_voice: "en_US-lessac-medium"

privacy:
  encrypted: true
  log_level: "info"

api:
  enabled: false
  host: "127.0.0.1"
  port: 8000
  cors_origins:
    - "http://localhost:3000"
```

### 2. .env file (Local overrides)

```bash
# .env (DO NOT commit to git)
JARVIS_DEBUG=true
JARVIS_DATA_DIR=/home/user/.jarvis/data
JARVIS_DB_PATH=/home/user/.jarvis/data/jarvis.db

# Master encryption key (critical!)
JARVIS_MASTER_KEY=your-32-byte-base64-key-here

# University credentials (optional)
JARVIS_MOODLE_URL=https://lms.youruni.edu
# Username/password prompted at runtime
```

### 3. Environment Variables (CI/Production)

```bash
# Production deployment
export JARVIS_DEBUG=false
export JARVIS_DATA_DIR=/opt/jarvis/data
export JARVIS_DB_PATH=/opt/jarvis/data/jarvis.db
export JARVIS_API_ENABLED=true
export JARVIS_API_HOST=0.0.0.0
export JARVIS_API_PORT=8000
```

---

## Environment Variable Reference

### Core Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JARVIS_DEBUG` | bool | false | Enable debug mode |
| `JARVIS_DATA_DIR` | path | "./data" | Data directory |
| `JARVIS_DB_PATH` | path | "{data_dir}/jarvis.db" | Database file |
| `JARVIS_LOG_LEVEL` | string | "info" | Log level |
| `JARVIS_LOG_DIR` | path | "{data_dir}/logs" | Log directory |

### Security

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JARVIS_MASTER_KEY` | string | null | Encryption master key |
| `JARVIS_API_KEY` | string | null | API authentication key |

### University

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JARVIS_UNIVERSITY_ENABLED` | bool | false | Enable university features |
| `JARVIS_UNIVERSITY_AUTO_SYNC` | bool | false | Auto-sync enabled |

### Voice

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JARVIS_VOICE_ENABLED` | bool | false | Enable voice |
| `JARVIS_VOICE_WAKE_WORD` | string | "hey jarvis" | Wake word |

### API

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JARVIS_API_ENABLED` | bool | false | Enable REST API |
| `JARVIS_API_HOST` | string | "127.0.0.1" | API host |
| `JARVIS_API_PORT` | int | 8000 | API port |

---

## Configuration Class

```python
# jarvis/utils/config.py

import os
import yaml
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class JarvisConfig(BaseSettings):
    """JARVIS configuration with env var support"""
    
    model_config = {
        "env_prefix": "JARVIS_",
        "env_nested_delimiter": "__",
        "extra": "ignore"
    }
    
    # Core
    debug: bool = False
    data_dir: Path = Field(default=Path("./data"))
    db_path: Optional[Path] = None
    
    # Security
    master_key: Optional[str] = Field(default=None, alias="JARVIS_MASTER_KEY")
    
    # Logging
    log_level: str = "info"
    log_dir: Optional[Path] = None
    
    # University
    university_enabled: bool = False
    university_auto_sync: bool = False
    
    # Voice
    voice_enabled: bool = False
    voice_wake_word: str = "hey jarvis"
    voice_stt_model: str = "base"
    
    # API
    api_enabled: bool = False
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    
    # User
    user_name: Optional[str] = None
    user_timezone: str = "UTC"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Apply YAML config (overridden by env vars)
        self._load_yaml_config()
        
        # Resolve paths
        self._resolve_paths()
    
    def _load_yaml_config(self):
        """Load settings from config.yaml"""
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f)
                self._apply_yaml(yaml_config)
    
    def _apply_yaml(self, config: dict, prefix: str = ""):
        """Apply YAML config to fields"""
        for key, value in config.items():
            if isinstance(value, dict):
                self._apply_yaml(value, f"{prefix}{key}_")
            else:
                env_key = f"{prefix}{key}".upper()
                if not hasattr(self, env_key) or getattr(self, env_key) is None:
                    setattr(self, env_key, value)
    
    def _resolve_paths(self):
        """Resolve path fields"""
        if self.db_path is None:
            self.db_path = self.data_dir / "jarvis.db"
        
        if self.log_dir is None:
            self.log_dir = self.data_dir / "logs"
    
    def ensure_directories(self):
        """Create necessary directories"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = JarvisConfig()
```

---

## Usage

### Basic Usage

```python
from jarvis.utils.config import config

# Access configuration
if config.debug:
    print("Debug mode enabled")

# Database path (auto-resolved)
print(f"Database: {config.db_path}")

# Environment variables override YAML
# JARVIS_DEBUG=true python script.py  # Overrides config.yaml
```

### In Application

```python
# jarvis/main.py

from jarvis.utils.config import config
from jarvis.utils.logger import setup_logger
from jarvis.db.database import Database

def main():
    # Ensure directories exist
    config.ensure_directories()
    
    # Setup logging
    logger = setup_logger(
        level=config.log_level,
        log_dir=config.log_dir,
        debug=config.debug
    )
    
    logger.info("Starting JARVIS")
    
    # Initialize database
    db = Database(path=config.db_path)
    db.initialize()
    
    # Start services based on config
    if config.voice_enabled:
        from jarvis.voice.interface import VoiceInterface
        voice = VoiceInterface()
        voice.start()
    
    if config.api_enabled:
        from jarvis.api.app import create_app
        import uvicorn
        app = create_app()
        uvicorn.run(app, host=config.api_host, port=config.api_port)
```

---

## Environment File Loading

```python
# jarvis/utils/config.py (add to __init__)

import os
from pathlib import Path

def _load_env_file():
    """Load .env file if present"""
    env_path = Path(".env")
    
    if not env_path.exists():
        return
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            
            # Parse KEY=value
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                # Only set if not already in environment
                if key not in os.environ:
                    os.environ[key] = value
```

---

## Validation

```python
from pydantic import validator

class JarvisConfig(BaseSettings):
    
    log_level: str = "info"
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.lower()
    
    api_port: int = 8000
    
    @validator("api_port")
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError(f"Invalid port: {v}")
        return v
```

---

## CLI Integration

```bash
# Show current config (with env overrides)
jarvis config show

# Show only from environment
jarvis config show --source env

# Set value
jarvis config set debug true
jarvis config set data_dir /path/to/data

# Reset to defaults
jarvis config reset
```

---

## Security Notes

| Secret | Storage | Recommendation |
|--------|---------|----------------|
| `JARVIS_MASTER_KEY` | Environment only | Never in config.yaml |
| `JARVIS_API_KEY` | Environment only | Rotate regularly |

### .gitignore

```
# Never commit
.env
*.db
*.db-journal
*.log
logs/
```

---

<div align="center">

**Configuration: Flexible, secure, portable.**

</div>
