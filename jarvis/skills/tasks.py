"""Task CRUD operations."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from jarvis.db.models import Task, TaskCreate, TaskUpdate, TaskStatus, TaskSource
from jarvis.db.database import Database
from jarvis.utils.logger import get_logger

logger = get_logger("skills.tasks")


class TaskService:
    """Service for task CRUD operations."""

    def __init__(self, db: Database):
        self.db = db

    def create(self, data: TaskCreate) -> Task:
        """Create a new task."""
        task = Task(
            id=str(uuid.uuid4()),
            title=data.title,
            description=data.description,
            energy_level=data.energy_level,
            deadline=data.deadline,
            priority=data.priority,
            status=TaskStatus.PENDING,
            source=data.source,
            tags=data.tags,
        )

        self.db.execute(
            """
            INSERT INTO tasks (id, title, description, energy_level, deadline, 
                             priority, status, source, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.id,
                task.title,
                task.description,
                task.energy_level,
                task.deadline.isoformat() if task.deadline else None,
                task.priority,
                task.status.value
                if isinstance(task.status, TaskStatus)
                else task.status,
                task.source.value
                if isinstance(task.source, TaskSource)
                else task.source,
                task.created_at.isoformat(),
                None,
            ),
        )

        logger.info(f"Task created: {task.id}", extra={"task_id": task.id})
        return task

    def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        row = self.db.query_one("SELECT * FROM tasks WHERE id = ?", (task_id,))

        if not row:
            return None

        return self._row_to_task(row)

    def list(
        self,
        status: Optional[TaskStatus] = None,
        source: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Task]:
        """List tasks with optional filters."""
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status.value if isinstance(status, TaskStatus) else status)

        if source:
            conditions.append("source = ?")
            params.append(source)

        where = " AND ".join(conditions) if conditions else "1=1"

        rows = self.db.query(
            f"""
            SELECT * FROM tasks 
            WHERE {where}
            ORDER BY 
                CASE WHEN deadline IS NULL THEN 1 ELSE 0 END,
                deadline ASC,
                priority DESC,
                created_at DESC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        )

        return [self._row_to_task(row) for row in rows]

    def count(self, status: Optional[TaskStatus] = None) -> int:
        """Count tasks."""
        if status:
            status_val = status.value if isinstance(status, TaskStatus) else status
            row = self.db.query_one(
                "SELECT COUNT(*) as count FROM tasks WHERE status = ?", (status_val,)
            )
        else:
            row = self.db.query_one("SELECT COUNT(*) as count FROM tasks")

        return row["count"] if row else 0

    def update(self, task_id: str, data: TaskUpdate) -> Optional[Task]:
        """Update a task."""
        updates = {}

        if data.title is not None:
            updates["title"] = data.title

        if data.description is not None:
            updates["description"] = data.description

        if data.energy_level is not None:
            updates["energy_level"] = data.energy_level

        if data.deadline is not None:
            updates["deadline"] = data.deadline.isoformat() if data.deadline else None

        if data.priority is not None:
            updates["priority"] = data.priority

        if data.status is not None:
            status_val = (
                data.status.value
                if isinstance(data.status, TaskStatus)
                else data.status
            )
            updates["status"] = status_val
            updates["completed_at"] = (
                datetime.now(timezone.utc).isoformat() if status_val == "completed" else None
            )

        if data.tags is not None:
            updates["tags"] = json.dumps(data.tags)

        if not updates:
            return self.get(task_id)

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        params = list(updates.values()) + [task_id]

        self.db.execute(
            f"UPDATE tasks SET {set_clause} WHERE id = ?", tuple(params)
        )

        logger.info(f"Task updated: {task_id}")
        return self.get(task_id)

    def complete(self, task_id: str) -> Optional[Task]:
        """Mark a task as completed."""
        return self.update(task_id, TaskUpdate(status=TaskStatus.COMPLETED))

    def cancel(self, task_id: str) -> Optional[Task]:
        """Mark a task as cancelled."""
        return self.update(task_id, TaskUpdate(status=TaskStatus.CANCELLED))

    def delete(self, task_id: str) -> bool:
        """Delete a task."""
        count = self.db.delete("tasks", "id = ?", (task_id,))

        if count > 0:
            logger.info(f"Task deleted: {task_id}")
            return True
        return False

    def get_due_today(self) -> list[Task]:
        """Get tasks due today."""
        today = datetime.now(timezone.utc).date().isoformat()
        rows = self.db.query(
            """
            SELECT * FROM tasks 
            WHERE deadline LIKE ? || '%'
            AND status = 'pending'
            ORDER BY deadline ASC
            """,
            (today,),
        )
        return [self._row_to_task(row) for row in rows]

    def _row_to_task(self, row) -> Task:
        """Convert database row to Task model."""
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            energy_level=row["energy_level"],
            deadline=datetime.fromisoformat(row["deadline"])
            if row["deadline"]
            else None,
            priority=row["priority"],
            status=row["status"],
            source=row["source"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else datetime.now(timezone.utc),
            completed_at=datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None,
        )
