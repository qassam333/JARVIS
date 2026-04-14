"""Database migrations system."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from datetime import datetime


class Migration(ABC):
    """Base class for database migrations."""

    version: str = ""
    description: str = ""

    @abstractmethod
    def up(self, db: "Database") -> None:
        """Apply the migration."""
        pass

    @abstractmethod
    def down(self, db: "Database") -> None:
        """Rollback the migration."""
        pass


class Database:
    """Placeholder for actual database - imported at runtime."""

    pass


class MigrationTracker:
    """Track applied migrations."""

    def __init__(self, db: Database):
        self.db = db

    def ensure_table(self) -> None:
        """Create migration tracking table if not exists."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)

    def get_applied(self) -> set[str]:
        """Get set of applied migration versions."""
        result = self.db.query("SELECT version FROM _migrations")
        return {row["version"] for row in result}

    def mark_applied(self, version: str, description: str) -> None:
        """Mark a migration as applied."""
        self.db.execute(
            "INSERT OR REPLACE INTO _migrations (version, description, applied_at) VALUES (?, ?, ?)",
            (version, description, datetime.utcnow()),
        )

    def mark_rolled_back(self, version: str) -> None:
        """Remove migration from applied list."""
        self.db.execute("DELETE FROM _migrations WHERE version = ?", (version,))


class MigrationRunner:
    """Execute migrations in order."""

    def __init__(self, db: Database, migrations_dir: Optional[Path] = None):
        self.db = db
        self.tracker = MigrationTracker(db)
        self.migrations_dir = migrations_dir or Path(__file__).parent / "scripts"

    def get_pending_migrations(self) -> list[Migration]:
        """Get migrations not yet applied."""
        applied = self.tracker.get_applied()

        from jarvis.db.migrations import scripts

        pending = []
        for migration in scripts.get_all_migrations():
            if migration.version not in applied:
                pending.append(migration)

        return sorted(pending, key=lambda m: m.version)

    def migrate(self) -> list[str]:
        """Run all pending migrations."""
        self.tracker.ensure_table()
        pending = self.get_pending_migrations()
        applied = []

        for migration in pending:
            print(f"Applying migration {migration.version}: {migration.description}")
            try:
                migration.up(self.db)
                self.tracker.mark_applied(migration.version, migration.description)
                applied.append(migration.version)
            except Exception as e:
                print(f"Migration {migration.version} failed: {e}")
                raise

        return applied

    def rollback(self, steps: int = 1) -> list[str]:
        """Rollback the last N migrations."""
        self.tracker.ensure_table()
        applied = self.tracker.get_applied()
        rolled_back = []

        for version in sorted(applied, reverse=True)[:steps]:
            from jarvis.db.migrations.scripts import get_migration_by_version

            migration = get_migration_by_version(version)
            if migration:
                print(f"Rolling back {migration.version}: {migration.description}")
                try:
                    migration.down(self.db)
                    self.tracker.mark_rolled_back(version)
                    rolled_back.append(version)
                except Exception as e:
                    print(f"Rollback {migration.version} failed: {e}")
                    raise

        return rolled_back
