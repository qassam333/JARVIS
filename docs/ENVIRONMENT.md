# Environment Variables Reference

> **Quick reference for all JARVIS environment variables.**

---

## Quick Reference Table

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JARVIS_DEBUG` | No | false | Enable debug mode |
| `JARVIS_DATA_DIR` | No | ./data | Data directory |
| `JARVIS_DB_PATH` | No | {data_dir}/jarvis.db | Database file path |
| `JARVIS_LOG_LEVEL` | No | info | Log level |
| `JARVIS_LOG_DIR` | No | {data_dir}/logs | Log directory |
| `JARVIS_MASTER_KEY` | V2 | - | Encryption master key |
| `JARVIS_USER_NAME` | No | - | Your name |
| `JARVIS_USER_TIMEZONE` | No | UTC | Your timezone |
| `JARVIS_UNIVERSITY_ENABLED` | No | false | Enable university |
| `JARVIS_UNIVERSITY_AUTO_SYNC` | No | false | Auto-sync |
| `JARVIS_VOICE_ENABLED` | No | false | Enable voice |
| `JARVIS_VOICE_WAKE_WORD` | No | hey jarvis | Wake phrase |
| `JARVIS_VOICE_STT_MODEL` | No | base | Whisper model |
| `JARVIS_API_ENABLED` | No | false | Enable REST API |
| `JARVIS_API_HOST` | No | 127.0.0.1 | API host |
| `JARVIS_API_PORT` | No | 8000 | API port |

---

## Examples

### Development

```bash
export JARVIS_DEBUG=true
export JARVIS_LOG_LEVEL=debug
export JARVIS_DATA_DIR=./data
```

### Production

```bash
export JARVIS_DEBUG=false
export JARVIS_DATA_DIR=/opt/jarvis/data
export JARVIS_LOG_LEVEL=warning
export JARVIS_API_ENABLED=true
export JARVIS_API_HOST=0.0.0.0
export JARVIS_API_PORT=8000
```

### With University

```bash
export JARVIS_UNIVERSITY_ENABLED=true
export JARVIS_UNIVERSITY_AUTO_SYNC=true
# Credentials prompted at runtime
```

### With Voice

```bash
export JARVIS_VOICE_ENABLED=true
export JARVIS_VOICE_WAKE_WORD="hey jarvis"
export JARVIS_VOICE_STT_MODEL=small  # Better accuracy
```

### .env File

```bash
# .env (DO NOT commit this file!)
JARVIS_DEBUG=true
JARVIS_DATA_DIR=./data
JARVIS_LOG_LEVEL=debug

# Security (for V2)
JARVIS_MASTER_KEY=your-32-byte-base64-encoded-key
```

---

## Priority Order

```
1. Environment Variables (highest)
2. .env file
3. config.yaml
4. Default values (lowest)
```

---

## Nested Variables

Use `__` for nested config:

```bash
export JARVIS_VOICE__STT_MODEL=small
export JARVIS_API__PORT=9000
```

---

<div align="center">

**Environment: Override anything, break nothing.**

</div>
