"""Tests for database operations."""

import pytest
from pathlib import Path
from jarvis.db.database import Database


@pytest.fixture
def db(tmp_path):
    """Create a fresh test database."""
    db = Database(tmp_path / "test.db")
    db.initialize()
    return db


class TestDatabaseInit:
    """Test database initialization."""

    def test_create_from_path(self, tmp_path):
        db = Database(tmp_path / "new.db")
        db.initialize()
        assert (tmp_path / "new.db").exists()

    def test_create_from_string(self, tmp_path):
        """Database should accept string paths (coercion fix)."""
        db = Database(str(tmp_path / "string.db"))
        db.initialize()
        assert (tmp_path / "string.db").exists()

    def test_create_from_none(self):
        """Database should default to ./data/jarvis.db."""
        db = Database(None)
        assert db.path == Path("./data/jarvis.db")

    def test_tables_created(self, db):
        tables = db.query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = {r["name"] for r in tables}
        assert "tasks" in table_names
        assert "notes" in table_names


class TestDatabaseOperations:
    """Test CRUD operations."""

    def test_insert_and_query(self, db):
        db.execute(
            "INSERT INTO tasks (id, title, status) VALUES (?, ?, ?)",
            ("test-1", "Test Task", "pending"),
        )
        result = db.query("SELECT * FROM tasks WHERE id = ?", ("test-1",))
        assert len(result) == 1
        assert result[0]["title"] == "Test Task"

    def test_query_one(self, db):
        db.execute(
            "INSERT INTO tasks (id, title, status) VALUES (?, ?, ?)",
            ("test-2", "Another Task", "pending"),
        )
        result = db.query_one("SELECT * FROM tasks WHERE id = ?", ("test-2",))
        assert result is not None
        assert result["title"] == "Another Task"

    def test_query_one_not_found(self, db):
        result = db.query_one("SELECT * FROM tasks WHERE id = ?", ("nonexistent",))
        assert result is None
