"""Migration 004: Daily Tasks System.

Creates daily_tasks table for daily task selection.
"""

from jarvis.db.migrations import Migration


class DailyTasksMigration(Migration):
    """Migration 004: Daily tasks system."""

    version = "004"
    description = "Daily task selection system"

    def up(self, db) -> None:
        """Create daily_tasks table."""
        db.execute("""
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                date DATE NOT NULL,
                selected_score REAL,
                status TEXT DEFAULT 'pending',
                original_deadline DATE,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                UNIQUE(date, task_id)
            )
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_tasks_date ON daily_tasks(date)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_tasks_status ON daily_tasks(status)
        """)

    def down(self, db) -> None:
        """Drop daily_tasks table."""
        db.execute("DROP INDEX IF EXISTS idx_daily_tasks_status")
        db.execute("DROP INDEX IF EXISTS idx_daily_tasks_date")
        db.execute("DROP TABLE IF EXISTS daily_tasks")


_MIGRATIONS = [
    DailyTasksMigration,
]
