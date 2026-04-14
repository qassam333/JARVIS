# Dependencies

> **JARVIS Python Dependencies**

---

## Core Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"

# Data Validation
pydantic = "^2.0"
pydantic-settings = "^2.0"

# Database
sqlalchemy = "^2.0"

# Encryption
cryptography = "^41.0"

# Configuration
pyyaml = "^6.0"

# CLI
rich = "^13.0"
click = "^8.1"

# HTTP (for university scraper)
httpx = "^0.25"
beautifulsoup4 = "^4.12"
lxml = "^4.9"
```

## Optional Dependencies

```toml
[tool.poetry.dependencies]

# Voice (optional)
pyaudio = { version = "^0.2", optional = true }
whisper = { version = "^1.0", optional = true }

# API (optional)
fastapi = { version = "^0.104", optional = true }
uvicorn = { version = "^0.24", optional = true }

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.21"
black = "^23.0"
ruff = "^0.1"
mypy = "^1.7"
```

## Installation Options

```bash
# Core only
poetry install

# With voice support
poetry install --extras voice

# With API support
poetry install --extras api

# Full installation
poetry install --all-extras
```

---

## Version Pinning Notes

| Package | Reason |
|---------|--------|
| python ^3.11 | Requires 3.11+ for some features |
| pydantic ^2.0 | Major version change, use v2 |
| sqlalchemy ^2.0 | Major version change, use v2 |

---

## Platform-Specific

```toml
[tool.poetry.group.voice]
optional = true

[tool.poetry.group.voice.dependencies]
pyaudio = "^0.2"

[tool.poetry.plugins.macOS.dependencies]
pyaudio = { version = "^0.2", platform = "darwin" }
```

---

<div align="center">

**Dependencies: Minimal by design.**

</div>
