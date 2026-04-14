"""Note CRUD operations."""

import json
import uuid
from datetime import datetime
from typing import Optional

from jarvis.db.models import Note, NoteCreate, NoteUpdate
from jarvis.db.database import Database
from jarvis.utils.logger import get_logger

logger = get_logger("skills.notes")


class NoteService:
    """Service for note CRUD operations."""

    def __init__(self, db: Database):
        self.db = db

    def create(self, data: NoteCreate) -> Note:
        """Create a new note."""
        now = datetime.utcnow()
        note = Note(
            id=str(uuid.uuid4()),
            title=data.title,
            content=data.content,
            tags=data.tags,
            created_at=now,
            updated_at=now,
        )

        self.db.execute(
            """
            INSERT INTO notes (id, title, content, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                note.id,
                note.title,
                note.content,
                json.dumps(note.tags),
                note.created_at.isoformat(),
                note.updated_at.isoformat(),
            ),
        )

        logger.info(f"Note created: {note.id}", extra={"note_id": note.id})
        return note

    def get(self, note_id: str) -> Optional[Note]:
        """Get a note by ID."""
        row = self.db.query_one("SELECT * FROM notes WHERE id = ?", (note_id,))

        if not row:
            return None

        return self._row_to_note(row)

    def list(self, tag: Optional[str] = None, limit: int = 100) -> list[Note]:
        """List notes with optional tag filter."""
        if tag:
            rows = self.db.query(
                """
                SELECT * FROM notes 
                WHERE tags LIKE ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (f'%"{tag}"%', limit),
            )
        else:
            rows = self.db.query(
                "SELECT * FROM notes ORDER BY updated_at DESC LIMIT ?", (limit,)
            )

        return [self._row_to_note(row) for row in rows]

    def search(self, query: str) -> list[Note]:
        """Search notes by title or content."""
        query_lower = f"%{query.lower()}%"
        rows = self.db.query(
            """
            SELECT * FROM notes 
            WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?
            ORDER BY updated_at DESC
            """,
            (query_lower, query_lower),
        )
        return [self._row_to_note(row) for row in rows]

    def update(self, note_id: str, data: NoteUpdate) -> Optional[Note]:
        """Update a note."""
        updates = ["updated_at = ?"]
        params = [datetime.utcnow().isoformat()]

        if data.title is not None:
            updates.append("title = ?")
            params.append(data.title)

        if data.content is not None:
            updates.append("content = ?")
            params.append(data.content)

        if data.tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(data.tags))

        params.append(note_id)

        self.db.execute(
            f"UPDATE notes SET {', '.join(updates)} WHERE id = ?", tuple(params)
        )

        logger.info(f"Note updated: {note_id}")
        return self.get(note_id)

    def delete(self, note_id: str) -> bool:
        """Delete a note."""
        count = self.db.delete("DELETE FROM notes WHERE id = ?", (note_id,))

        if count > 0:
            logger.info(f"Note deleted: {note_id}")
            return True
        return False

    def _row_to_note(self, row) -> Note:
        """Convert database row to Note model."""
        return Note(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else datetime.utcnow(),
            updated_at=datetime.fromisoformat(row["updated_at"])
            if row["updated_at"]
            else datetime.utcnow(),
        )
