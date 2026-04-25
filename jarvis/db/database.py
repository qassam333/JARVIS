"""SQLite database connection and operations."""

import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional
from contextlib import contextmanager

from jarvis.utils.logger import get_logger

logger = get_logger("db")


class Database:
    """SQLite database wrapper."""

    def __init__(self, path: Optional[Path] = None):
        if isinstance(path, str):
            path = Path(path)
        self.path = path or Path("./data/jarvis.db")
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure database directory exists."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.path), check_same_thread=False
            )
            self._connection.row_factory = self._dict_factory
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    @staticmethod
    def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
        """Convert row to dictionary with column names."""
        return {col[0]: row[i] for i, col in enumerate(cursor.description)}

    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        with self._lock:
            conn = self._get_connection()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL statement."""
        with self.get_session() as conn:
            cursor = conn.execute(sql, params)
            return cursor

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Query and return results."""
        with self.get_session() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchall()

    def query_one(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Query and return single result."""
        with self.get_session() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()

    def insert(self, table: str, data: dict[str, Any]) -> str:
        """Insert a row and return the id."""
        columns = list(data.keys())
        placeholders = ",".join(["?" for _ in columns])
        columns_str = ",".join(columns)

        sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

        with self.get_session() as conn:
            cursor = conn.execute(sql, tuple(data.values()))
            return cursor.lastrowid

    def update(
        self, table: str, data: dict[str, Any], where: str, params: tuple = ()
    ) -> int:
        """Update rows and return count."""
        set_clause = ",".join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

        with self.get_session() as conn:
            cursor = conn.execute(sql, tuple(data.values()) + params)
            return cursor.rowcount

    def delete(self, table: str, where: str, params: tuple = ()) -> int:
        """Delete rows and return count."""
        sql = f"DELETE FROM {table} WHERE {where}"

        with self.get_session() as conn:
            cursor = conn.execute(sql, params)
            return cursor.rowcount

    def initialize(self) -> None:
        """Initialize database with migrations."""
        from jarvis.db.migrations import MigrationRunner

        logger.info("Initializing database")

        runner = MigrationRunner(self)
        applied = runner.migrate()

        if applied:
            logger.info(f"Applied migrations: {', '.join(applied)}")
        else:
            logger.info("Database already up to date")

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def backup(self, path: Path) -> None:
        """Create database backup."""
        import shutil

        shutil.copy2(self.path, path)
        logger.info(f"Database backed up to {path}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
