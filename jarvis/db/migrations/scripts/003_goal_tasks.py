"""Migration 003: Goal Task Linking.

Adds goal_id to tasks table for bidirectional linking.
"""

from jarvis.db.migrations import Migration


class GoalTasksMigration(Migration):
    """Migration 003: Goal task linking."""

    version = "003"
    description = "Add goal_id to tasks for goal-task linking"

    def up(self, db) -> None:
        """Add goal_id column to tasks."""
        db.execute("""
            ALTER TABLE tasks 
            ADD COLUMN goal_id TEXT REFERENCES goals(id)
        """)
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_goal ON tasks(goal_id)
        """)

    def down(self, db) -> None:
        """Remove goal_id column from tasks."""
        db.execute("DROP INDEX IF EXISTS idx_tasks_goal")
        db.execute("ALTER TABLE tasks DROP COLUMN goal_id")


_MIGRATIONS = [
    GoalTasksMigration,
]
