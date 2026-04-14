"""Knowledge CRUD operations."""

import json
import uuid
from datetime import datetime
from typing import Optional

from jarvis.db.models import Knowledge, KnowledgeCreate, KnowledgeUpdate
from jarvis.db.database import Database
from jarvis.utils.logger import get_logger

logger = get_logger("skills.knowledge")


class KnowledgeService:
    """Service for knowledge CRUD operations."""

    def __init__(self, db: Database):
        self.db = db

    def create(self, data: KnowledgeCreate) -> Knowledge:
        """Add new knowledge."""
        knowledge = Knowledge(
            id=str(uuid.uuid4()),
            fact=data.fact,
            category=data.category,
            source=data.source,
            tags=data.tags,
            created_at=datetime.utcnow(),
        )

        self.db.execute(
            """
            INSERT INTO knowledge (id, fact, category, source, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                knowledge.id,
                knowledge.fact,
                knowledge.category,
                knowledge.source,
                json.dumps(knowledge.tags),
                knowledge.created_at.isoformat(),
            ),
        )

        logger.info(
            f"Knowledge added: {knowledge.id}", extra={"knowledge_id": knowledge.id}
        )
        return knowledge

    def get(self, knowledge_id: str) -> Optional[Knowledge]:
        """Get knowledge by ID."""
        row = self.db.query_one("SELECT * FROM knowledge WHERE id = ?", (knowledge_id,))

        if not row:
            return None

        return self._row_to_knowledge(row)

    def list(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 100,
    ) -> list[Knowledge]:
        """List knowledge with optional filters."""
        conditions = []
        params = []

        if category:
            conditions.append("category = ?")
            params.append(category)

        if tag:
            conditions.append("tags LIKE ?")
            params.append(f'%"{tag}"%')

        where = " AND ".join(conditions) if conditions else "1=1"

        rows = self.db.query(
            f"SELECT * FROM knowledge WHERE {where} ORDER BY created_at DESC LIMIT ?",
            (*params, limit),
        )

        return [self._row_to_knowledge(row) for row in rows]

    def search(self, query: str) -> list[Knowledge]:
        """Search knowledge."""
        query_lower = f"%{query.lower()}%"
        rows = self.db.query(
            """
            SELECT * FROM knowledge 
            WHERE LOWER(fact) LIKE ? OR LOWER(category) LIKE ?
            ORDER BY created_at DESC
            """,
            (query_lower, query_lower),
        )
        return [self._row_to_knowledge(row) for row in rows]

    def update(self, knowledge_id: str, data: KnowledgeUpdate) -> Optional[Knowledge]:
        """Update knowledge."""
        updates = []
        params = []

        if data.fact is not None:
            updates.append("fact = ?")
            params.append(data.fact)

        if data.category is not None:
            updates.append("category = ?")
            params.append(data.category)

        if data.source is not None:
            updates.append("source = ?")
            params.append(data.source)

        if data.tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(data.tags))

        if not updates:
            return self.get(knowledge_id)

        params.append(knowledge_id)

        self.db.execute(
            f"UPDATE knowledge SET {', '.join(updates)} WHERE id = ?", tuple(params)
        )

        logger.info(f"Knowledge updated: {knowledge_id}")
        return self.get(knowledge_id)

    def delete(self, knowledge_id: str) -> bool:
        """Delete knowledge."""
        count = self.db.delete("DELETE FROM knowledge WHERE id = ?", (knowledge_id,))

        if count > 0:
            logger.info(f"Knowledge deleted: {knowledge_id}")
            return True
        return False

    def _row_to_knowledge(self, row) -> Knowledge:
        """Convert database row to Knowledge model."""
        return Knowledge(
            id=row["id"],
            fact=row["fact"],
            category=row["category"],
            source=row["source"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else datetime.utcnow(),
        )
