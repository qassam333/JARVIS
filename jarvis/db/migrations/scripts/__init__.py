"""Migration scripts registry."""

from typing import TYPE_CHECKING
from jarvis.db.migrations import Migration

if TYPE_CHECKING:
    from jarvis.db.database import Database


class InitialSchemaMigration(Migration):
    """Migration 001: Initial database schema."""

    version = "001"
    description = "Initial schema - tasks, notes, knowledge, university tables"

    def up(self, db: "Database") -> None:
        """Create initial tables."""
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                energy_level INTEGER,
                deadline TIMESTAMP,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                source TEXT DEFAULT 'manual',
                tags TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                fact TEXT NOT NULL,
                category TEXT,
                source TEXT,
                tags TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                date DATE PRIMARY KEY,
                energy_level INTEGER,
                productivity_score INTEGER,
                notes TEXT
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id TEXT PRIMARY KEY,
                service TEXT NOT NULL,
                username TEXT,
                encrypted_password BLOB,
                encrypted_token BLOB,
                base_url TEXT NOT NULL,
                last_sync TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                credentials_id TEXT,
                name TEXT NOT NULL,
                code TEXT,
                semester TEXT,
                instructor TEXT,
                FOREIGN KEY (credentials_id) REFERENCES credentials(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS university_assignments (
                id TEXT PRIMARY KEY,
                course_id TEXT,
                title TEXT NOT NULL,
                type TEXT,
                description TEXT,
                due_date TIMESTAMP,
                url TEXT,
                status TEXT DEFAULT 'pending',
                task_id TEXT,
                raw_data TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS sync_logs (
                id TEXT PRIMARY KEY,
                sync_type TEXT NOT NULL,
                status TEXT NOT NULL,
                items_synced INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY,
                name TEXT,
                preferences TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def down(self, db: "Database") -> None:
        """Drop all tables."""
        tables = [
            "university_assignments",
            "courses",
            "credentials",
            "sync_logs",
            "knowledge",
            "notes",
            "tasks",
            "daily_logs",
            "profile",
            "_migrations",
        ]

        for table in tables:
            db.execute(f"DROP TABLE IF EXISTS {table}")


_MIGRATIONS: list[type[Migration]] = [
    InitialSchemaMigration,
]


def _load_migration(name: str):
    """Lazy load a migration by filename."""
    try:
        import sys
        from pathlib import Path

        migration_path = Path(__file__).parent / name
        if migration_path.exists():
            import importlib.util

            spec = importlib.util.spec_from_file_location(name, migration_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
                return module
    except Exception:
        pass
    return None


def _load_life_migration():
    """Lazy load the life management migration."""
    module = _load_migration("002_life_management.py")
    return module.LifeManagementMigration if module else None


def _load_goal_tasks_migration():
    """Lazy load the goal tasks migration."""
    module = _load_migration("003_goal_tasks.py")
    return module.GoalTasksMigration if module else None


def _load_daily_tasks_migration():
    """Lazy load the daily tasks migration."""
    module = _load_migration("004_daily_tasks.py")
    return module.DailyTasksMigration if module else None


def get_all_migrations() -> list[Migration]:
    """Get all migration instances."""
    migrations = [m() for m in _MIGRATIONS]

    life_migration = _load_life_migration()
    if life_migration:
        migrations.append(life_migration())

    goal_tasks_migration = _load_goal_tasks_migration()
    if goal_tasks_migration:
        migrations.append(goal_tasks_migration())

    daily_tasks_migration = _load_daily_tasks_migration()
    if daily_tasks_migration:
        migrations.append(daily_tasks_migration())

    return migrations


def get_migration_by_version(version: str) -> Migration | None:
    """Get migration by version."""
    for m in get_all_migrations():
        if m.version == version:
            return m
    return None
