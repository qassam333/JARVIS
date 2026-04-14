# Database Layer Documentation

> **Purpose**: Persistent storage with encryption for sensitive data.

---

## Overview

The database layer provides:
1. **Persistent storage** - Data survives restarts
2. **Structured organization** - Tables for different data types
3. **Encryption** - Sensitive fields protected at rest
4. **ORM abstraction** - Clean Python interface

```
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                           │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  SQLite Database                     │   │
│  │   • Single file: jarvis.db                         │   │
│  │   • Located in ./data/                            │   │
│  │   • Portable (copy to backup)                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SQLAlchemy ORM                         │   │
│  │   • Models defined in Python                      │   │
│  │   • Type-safe queries                             │   │
│  │   • Migrations support                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Encryption Layer                        │   │
│  │   • Fernet (AES-128-CBC)                          │   │
│  │   • Encrypts: passwords, tokens                   │   │
│  │   • Key derived from master password              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
jarvis/
└── db/
    ├── __init__.py       # Exports
    ├── database.py       # Connection & session management
    ├── models.py         # SQLAlchemy ORM models
    ├── schema.py         # Raw SQL schema (reference)
    └── encryption.py     # Fernet encryption utilities
```

---

## Models

### Task Model

```python
class Task(Base):
    """Personal task or to-do item"""
    
    __tablename__ = "tasks"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    energy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    source: Mapped[str] = mapped_column(String(20), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

**Fields Explained**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID string | Unique identifier |
| `title` | string | What needs to be done |
| `description` | text | Additional details |
| `energy_level` | int (1-10) | Energy required to complete |
| `deadline` | datetime | When it's due |
| `priority` | int (1-5) | User-set priority |
| `status` | enum | pending, completed, cancelled |
| `source` | enum | manual, moodle, schedule |
| `created_at` | datetime | When created |
| `completed_at` | datetime | When marked done |

### Note Model

```python
class Note(Base):
    """Markdown note"""
    
    __tablename__ = "notes"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Knowledge Model

```python
class Knowledge(Base):
    """Fact or piece of knowledge"""
    
    __tablename__ = "knowledge"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    fact: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### Credentials Model

```python
class Credentials(Base):
    """University login credentials (encrypted)"""
    
    __tablename__ = "credentials"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    service: Mapped[str] = mapped_column(String(50), nullable=False)  # "moodle"
    username: Mapped[str | None] = mapped_column(String(200), nullable=True)
    encrypted_password: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    encrypted_token: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    last_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**Critical**: `encrypted_password` and `encrypted_token` are **bytes** (encrypted), not strings.

### UniversityAssignment Model

```python
class UniversityAssignment(Base):
    """Assignment imported from university LMS"""
    
    __tablename__ = "university_assignments"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(20))  # assignment, quiz, exam, lecture
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### Course Model

```python
class Course(Base):
    """University course"""
    
    __tablename__ = "courses"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    credentials_id: Mapped[str] = mapped_column(String(36), ForeignKey("credentials.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    semester: Mapped[str | None] = mapped_column(String(50), nullable=True)
    instructor: Mapped[str | None] = mapped_column(String(100), nullable=True)
```

### DailyLog Model

```python
class DailyLog(Base):
    """Daily context tracking"""
    
    __tablename__ = "daily_logs"
    
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    energy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    productivity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

---

## Database Operations

### Session Management

```python
from jarvis.db.database import Database

db = Database()
db.initialize()  # Creates tables if not exist

# Get session for operations
with db.get_session() as session:
    # Query
    tasks = session.query(Task).filter(Task.status == "pending").all()
    
    # Create
    task = Task(id="uuid", title="New task")
    session.add(task)
    session.commit()
```

### CRUD Operations Example

```python
from jarvis.db.models import Task
from jarvis.db.database import Database
import uuid

db = Database()

# CREATE
def add_task(title: str, energy_level: int = 5) -> Task:
    with db.get_session() as session:
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            energy_level=energy_level,
            status="pending"
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

# READ
def get_pending_tasks() -> list[Task]:
    with db.get_session() as session:
        return session.query(Task).filter(Task.status == "pending").all()

# UPDATE
def complete_task(task_id: str):
    with db.get_session() as session:
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            session.commit()

# DELETE
def delete_task(task_id: str):
    with db.get_session() as session:
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            session.delete(task)
            session.commit()
```

---

## Encryption Layer

### Purpose

Protect sensitive data stored in the database:
- University passwords
- Session tokens
- Future: user notes (optional)

### How Fernet Works

```python
from jarvis.db.encryption import Encryption

enc = Encryption(master_key="your-32-byte-base64-key")

# Encrypt sensitive data
encrypted = enc.encrypt("my_password")
# Returns: b'gAAAAABh...' (bytes)

# Decrypt when needed
decrypted = enc.decrypt(encrypted)
# Returns: "my_password"
```

### Key Generation

```python
from cryptography.fernet import Fernet

# Generate once
key = Fernet.generate_key()  # 32-byte URL-safe base64
# Store this in config.yaml
```

### Secure Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                 ENCRYPTION WORKFLOW                          │
│                                                              │
│  1. First Run:                                              │
│     • User provides master password                         │
│     • System derives encryption key                         │
│     • Key stored in config.yaml (encrypted at rest)         │
│                                                              │
│  2. Saving Credentials:                                     │
│     • User enters Moodle password                           │
│     • Password encrypted with Fernet                        │
│     • Encrypted bytes stored in database                    │
│                                                              │
│  3. Retrieving Credentials:                                 │
│     • Read encrypted bytes from database                    │
│     • Decrypt with Fernet                                   │
│     • Use for authentication                                 │
│                                                              │
│  4. Password never stored in plaintext                     │
└─────────────────────────────────────────────────────────────┘
```

### Encryption Class

```python
class Encryption:
    """Fernet encryption wrapper"""
    
    def __init__(self, master_key: str):
        """
        Args:
            master_key: Base64-encoded 32-byte key
        """
        self.fernet = Fernet(master_key.encode())
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt string to bytes"""
        return self.fernet.encrypt(data.encode())
    
    def decrypt(self, data: bytes) -> str:
        """Decrypt bytes to string"""
        return self.fernet.decrypt(data).decode()
```

---

## Schema Reference (Raw SQL)

For reference and migrations:

```sql
-- Tasks table
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    energy_level INTEGER,
    deadline TIMESTAMP,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    source TEXT DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Notes table
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    title TEXT,
    content TEXT NOT NULL,
    tags JSON DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge table
CREATE TABLE knowledge (
    id TEXT PRIMARY KEY,
    fact TEXT NOT NULL,
    category TEXT,
    source TEXT,
    tags JSON DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Credentials table (encrypted)
CREATE TABLE credentials (
    id TEXT PRIMARY KEY,
    service TEXT NOT NULL,
    username TEXT,
    encrypted_password BLOB,
    encrypted_token BLOB,
    base_url TEXT NOT NULL,
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Courses table
CREATE TABLE courses (
    id TEXT PRIMARY KEY,
    credentials_id TEXT,
    name TEXT NOT NULL,
    code TEXT,
    semester TEXT,
    instructor TEXT,
    FOREIGN KEY (credentials_id) REFERENCES credentials(id)
);

-- University assignments
CREATE TABLE university_assignments (
    id TEXT PRIMARY KEY,
    course_id TEXT,
    title TEXT NOT NULL,
    type TEXT,
    description TEXT,
    due_date TIMESTAMP,
    url TEXT,
    status TEXT DEFAULT 'pending',
    task_id TEXT,
    raw_data JSON,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Daily logs
CREATE TABLE daily_logs (
    date DATE PRIMARY KEY,
    energy_level INTEGER,
    productivity_score INTEGER,
    notes TEXT
);
```

---

## Migration Support

### Why Migrations?

As the project evolves, database schema may change:
- Add new columns
- Change data types
- Create new tables

### Migration Approach

```python
# jarvis/db/migrations.py

MIGRATIONS = {
    "001_initial": [
        "CREATE TABLE tasks (...)",
        "CREATE TABLE notes (...)",
        # ...
    ],
    "002_add_courses": [
        "CREATE TABLE courses (...)",
        "CREATE TABLE university_assignments (...)",
    ],
}

def run_migrations():
    """Run any pending migrations"""
    for version, sql_statements in MIGRATIONS.items():
        if not is_applied(version):
            for statement in sql_statements:
                execute(statement)
            mark_applied(version)
```

---

## Why Not Use Django ORM?

| Aspect | SQLAlchemy | Django ORM |
|--------|------------|------------|
| Framework coupling | Loose | Tight (Django required) |
| Learning curve | Moderate | Lower |
| Flexibility | Higher | Lower |
| Overhead | Minimal | Larger |

**Decision**: SQLAlchemy for flexibility and loose coupling.

---

## Backup & Recovery

### Manual Backup

```bash
# Copy database file
cp ./data/jarvis.db ./data/jarvis_backup_$(date +%Y%m%d).db
```

### Recovery

```bash
# Restore from backup
cp ./data/jarvis_backup_20240115.db ./data/jarvis.db
```

### Automated Backup (Future)

```python
# Scheduled backup
def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(DB_PATH, f"backup/jarvis_{timestamp}.db")
```

---

## Troubleshooting

### Database Locked Error

```
sqlite3.OperationalError: database is locked
```

**Solution**: Only one writer at a time. Ensure previous sessions closed.

### Corrupted Database

**Solution**: Restore from backup. Keep regular backups.

### Encryption Key Lost

**Problem**: Master key lost = encrypted data unrecoverable.

**Solution**: 
- Store key securely
- Backup key separately
- Future: key recovery mechanism

---

<div align="center">

**Data stays yours.**

</div>
