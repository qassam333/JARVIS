# Migration System

> **Purpose**: Safely evolve database schema without losing data.

---

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MIGRATION SYSTEM                          │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  SCHEMA_V1   │───▶│  Migration_2 │───▶│  SCHEMA_V2   │ │
│  │  (Current)   │    │  (Add Table) │    │  (New)       │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                              │
│  migrations/                                                │
│  ├── 001_initial.sql          # Creates all tables          │
│  ├── 002_add_tags.sql        # Adds tags column            │
│  └── 003_...sql              # Future migrations           │
│                                                              │
│  migration_tracker table:                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ version | applied_at | description                   │   │
│  │ 001     | 2024-01-01  | Initial schema               │   │
│  │ 002     | 2024-01-15  | Add tags to notes            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
jarvis/
└── db/
    └── migrations/
        ├── __init__.py
        ├── runner.py          # Migration executor
        ├── tracker.py          # Track applied migrations
        └── scripts/
            ├── 001_initial.py
            ├── 002_add_tags.py
            └── ...
```

---

## Migration Script Format

```python
# migrations/scripts/001_initial.py

"""
Migration 001: Initial Schema
Created: 2024-01-01
Description: Creates all initial tables
"""

from migrations.base import Migration

class Migration001(Migration):
    version = "001"
    description = "Initial schema"
    
    def up(self):
        """Apply migration"""
        self.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
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
        """)
        
        self.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT NOT NULL,
                tags JSON DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # ... more tables
    
    def down(self):
        """Rollback migration"""
        self.execute("DROP TABLE IF EXISTS tasks;")
        self.execute("DROP TABLE IF EXISTS notes;")
```

---

## Migration Runner

```python
# migrations/runner.py

class MigrationRunner:
    """Executes migrations in order"""
    
    def __init__(self, db: Database):
        self.db = db
        self._ensure_tracker_table()
    
    def _ensure_tracker_table(self):
        """Create migration tracking table"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
        """)
    
    def get_applied_versions(self) -> set[str]:
        """Get list of applied migration versions"""
        result = self.db.query("SELECT version FROM _migrations")
        return {row[0] for row in result}
    
    def get_pending_migrations(self) -> list[Migration]:
        """Get migrations not yet applied"""
        applied = self.get_applied_versions()
        pending = []
        
        for script in self._discover_migrations():
            if script.version not in applied:
                pending.append(script)
        
        return sorted(pending, key=lambda m: m.version)
    
    def migrate(self) -> list[str]:
        """Run all pending migrations"""
        pending = self.get_pending_migrations()
        applied = []
        
        for migration in pending:
            print(f"Applying migration {migration.version}...")
            migration.up()
            
            self.db.execute(
                "INSERT INTO _migrations (version, description) VALUES (?, ?)",
                (migration.version, migration.description)
            )
            
            applied.append(migration.version)
        
        return applied
    
    def rollback(self, steps: int = 1):
        """Rollback last N migrations"""
        applied = self.get_applied_versions()
        
        for version in sorted(applied, reverse=True)[:steps]:
            migration = self._load_migration(version)
            print(f"Rolling back {migration.version}...")
            migration.down()
            
            self.db.execute(
                "DELETE FROM _migrations WHERE version = ?",
                (version,)
            )
```

---

## Usage

```python
from jarvis.db.migrations import MigrationRunner

runner = MigrationRunner(db)
applied = runner.migrate()

if applied:
    print(f"Applied: {', '.join(applied)}")
else:
    print("Database up to date")
```

---

## CLI Integration

```bash
# Apply pending migrations
jarvis db migrate

# Show migration status
jarvis db status

# Rollback last migration
jarvis db rollback

# Rollback 2 migrations
jarvis db rollback --steps 2
```

---

## Rules

1. **Never modify applied migrations** - creates new migration instead
2. **Always implement `up()` and `down()`** - enables rollback
3. **Test migrations** - especially rollback logic
4. **Keep migrations small** - one logical change per migration

---

<div align="center">

**Migrate early, migrate often, lose nothing.**

</div>
