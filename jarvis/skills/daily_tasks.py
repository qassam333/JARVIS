"""Daily task selection service.

Handles daily task generation, prioritization, and rollover.
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from jarvis.db.database import Database
from jarvis.utils.logger import get_logger

logger = get_logger("skills.daily_tasks")


@dataclass
class DailyTask:
    id: str
    task_id: str
    date: date
    selected_score: float
    status: str
    original_deadline: Optional[date]
    completed_at: Optional[datetime]


@dataclass
class ScoredTask:
    task_id: str
    title: str
    goal_id: Optional[str]
    priority: int
    energy_level: int
    deadline: Optional[datetime]
    created_at: datetime
    score: float
    is_overdue: bool
    days_until_deadline: int
    seq_order: int


class DailyTaskService:
    DEADLINE_URGENCY_BOOST = 2.0
    OVERDUE_PENALTY = 3.0
    SEQUENTIAL_BONUS = 1.0
    DEFAULT_DAILY_LIMIT = 5

    def __init__(self, db: Database):
        self.db = db

    def calculate_priority_score(
        self,
        task_row: dict,
        today: date = None,
    ) -> float:
        """Calculate dynamic priority score for a task.

        Score = base_priority + deadline_urgency + overdue_penalty + sequential_bonus
        """
        if today is None:
            today = date.today()

        base_priority = float(task_row.get("priority", 1))
        deadline = task_row.get("deadline")

        if not deadline:
            return base_priority

        if isinstance(deadline, str):
            deadline = datetime.fromisoformat(deadline).date()

        days_until = (deadline - today).days
        is_overdue = days_until < 0
        is_due_soon = days_until <= 7

        score = base_priority

        if days_until <= 0:
            score += self.OVERDUE_PENALTY * abs(days_until)
        elif is_due_soon:
            urgency = (7 - days_until) / 7.0
            score += self.DEADLINE_URGENCY_BOOST * urgency

        return score

    def get_task_sequence_order(self, task_id: str) -> int:
        """Get the sequence order of a task within its goal."""
        row = self.db.query_one(
            "SELECT goal_id FROM tasks WHERE id = ?",
            (task_id,),
        )
        if not row or not row.get("goal_id"):
            return 999

        rows = self.db.query(
            """SELECT id FROM tasks 
               WHERE goal_id = ? 
               ORDER BY deadline ASC""",
            (row["goal_id"],),
        )

        for i, r in enumerate(rows):
            if r["id"] == task_id:
                return i

        return 999

    def get_available_tasks(
        self,
        today: date = None,
        goal_id: Optional[str] = None,
    ) -> list[ScoredTask]:
        """Get all pending tasks that could be selected for today."""
        if today is None:
            today = date.today()

        conditions = ["t.status = 'pending'"]
        params = []

        if goal_id:
            conditions.append("t.goal_id = ?")
            params.append(goal_id)

        where = " AND ".join(conditions)

        query = f"""
            SELECT t.id, t.title, t.goal_id, t.priority, t.energy_level,
                   t.deadline, t.created_at
            FROM tasks t
            WHERE {where}
            ORDER BY t.deadline ASC NULLS LAST
        """

        available = []
        for row in self.db.query(query, tuple(params)):
            score = self.calculate_priority_score(dict(row), today)
            deadline = row.get("deadline")
            days_until = 0
            is_overdue = False

            if deadline:
                if isinstance(deadline, str):
                    dl = datetime.fromisoformat(deadline).date()
                else:
                    dl = deadline
                days_until = (dl - today).days
                is_overdue = days_until < 0

            seq_order = self.get_task_sequence_order(row["id"])

            available.append(
                ScoredTask(
                    task_id=row["id"],
                    title=row["title"],
                    goal_id=row.get("goal_id"),
                    priority=row.get("priority", 1),
                    energy_level=row.get("energy_level", 5),
                    deadline=deadline,
                    created_at=row.get("created_at"),
                    score=score,
                    is_overdue=is_overdue,
                    days_until_deadline=days_until,
                    seq_order=seq_order,
                )
            )

        return available

    def check_sequential_unlock(self, task_id: str, today: date = None) -> bool:
        """Check if previous task in sequence is completed to unlock this one."""
        if today is None:
            today = date.today()

        row = self.db.query_one(
            "SELECT goal_id FROM tasks WHERE id = ?",
            (task_id,),
        )
        if not row or not row.get("goal_id"):
            return True

        goal_id = row["goal_id"]

        rows = self.db.query(
            """SELECT id, status FROM tasks 
               WHERE goal_id = ? AND status = 'pending'
               ORDER BY deadline ASC""",
            (goal_id,),
        )

        first_pending = rows[0]["id"] if rows else None

        return task_id == first_pending

    def select_daily_tasks(
        self,
        target_date: date = None,
        limit: int = None,
    ) -> list[ScoredTask]:
        """Select tasks for a specific date based on priority and sequence."""
        if target_date is None:
            target_date = date.today()

        if limit is None:
            limit = self.DEFAULT_DAILY_LIMIT

        available = self.get_available_tasks(target_date)

        selected = []
        seen_goals = set()

        for task in available:
            if len(selected) >= limit:
                break

            if task.goal_id and task.goal_id in seen_goals:
                continue

            if task.seq_order > 0:
                if not self.check_sequential_unlock(task.task_id, target_date):
                    logger.debug(f"Task {task.task_id} locked - waiting for previous")
                    continue

            if task.goal_id:
                seen_goals.add(task.goal_id)

            selected.append(task)

        return selected

    def generate_daily(
        self,
        target_date: date = None,
        limit: int = None,
    ) -> list[str]:
        """Generate daily tasks for a date."""
        if target_date is None:
            target_date = date.today()

        if limit is None:
            limit = self.DEFAULT_DAILY_LIMIT

        existing = self.db.query_one(
            "SELECT COUNT(*) as c FROM daily_tasks WHERE date = ?",
            (target_date.isoformat(),),
        )
        if existing and existing["c"] > 0:
            logger.info(f"Daily tasks already exist for {target_date}")
            return []

        tasks = self.select_daily_tasks(target_date, limit)

        task_ids = []
        for task in tasks:
            dt_id = str(uuid.uuid4())

            original_deadline = None
            if task.deadline:
                if isinstance(task.deadline, str):
                    original_deadline = datetime.fromisoformat(task.deadline).date()
                else:
                    original_deadline = task.deadline

            self.db.execute(
                """INSERT INTO daily_tasks 
                   (id, task_id, date, selected_score, original_deadline)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    dt_id,
                    task.task_id,
                    target_date.isoformat(),
                    task.score,
                    original_deadline.isoformat() if original_deadline else None,
                ),
            )

            task_ids.append(dt_id)
            logger.info(f"Selected: {task.title} (score: {task.score:.2f})")

        logger.info(f"Generated {len(task_ids)} daily tasks for {target_date}")
        return task_ids

    def roll_over_undone(
        self,
        from_date: date = None,
        to_date: date = None,
    ) -> int:
        """Roll over undone tasks to another date."""
        if from_date is None:
            from_date = date.today()

        if to_date is None:
            to_date = from_date + timedelta(days=1)

        rows = self.db.query(
            """SELECT dt.id, dt.task_id, dt.selected_score
               FROM daily_tasks dt
               WHERE dt.date = ? AND dt.status = 'pending'""",
            (from_date.isoformat(),),
        )

        rolled = 0
        for row in rows:
            existing = self.db.query_one(
                """SELECT id FROM daily_tasks 
                   WHERE date = ? AND task_id = ?""",
                (to_date.isoformat(), row["task_id"]),
            )

            if existing:
                continue

            self.db.execute(
                """UPDATE daily_tasks 
                   SET date = ?, status = 'pending'
                   WHERE id = ?""",
                (to_date.isoformat(), row["id"]),
            )
            rolled += 1

        logger.info(f"Rolled over {rolled} tasks to {to_date}")
        return rolled

    def mark_done(self, task_id: str, target_date: date = None) -> bool:
        """Mark a daily task as done."""
        if target_date is None:
            target_date = date.today()

        task_row = self.db.query_one(
            "SELECT id, task_id FROM daily_tasks WHERE task_id LIKE ? AND date = ?",
            (f"{task_id}%", target_date.isoformat()),
        )

        if not task_row:
            logger.warning(f"Task not found: {task_id}")
            return False

        self.db.execute(
            """UPDATE daily_tasks 
               SET status = 'done', completed_at = ?
               WHERE id = ?""",
            (datetime.now().isoformat(), task_row["id"]),
        )

        self.db.execute(
            """UPDATE tasks 
               SET status = 'completed', completed_at = ?
               WHERE id = ?""",
            (datetime.now().isoformat(), task_row["task_id"]),
        )

        logger.info(f"Task {task_row['task_id']} marked as done")
        return True

    def get_daily_tasks(
        self,
        target_date: date = None,
        status: str = None,
    ) -> list[DailyTask]:
        """Get daily tasks for a date."""
        if target_date is None:
            target_date = date.today()

        conditions = ["date = ?"]
        params = [target_date.isoformat()]

        if status:
            conditions.append("status = ?")
            params.append(status)

        where = " AND ".join(conditions)

        rows = self.db.query(
            f"""SELECT id, task_id, date, selected_score, status, 
                   original_deadline, completed_at
            FROM daily_tasks 
            WHERE {where}
            ORDER BY selected_score DESC""",
            tuple(params),
        )

        return [DailyTask(**dict(row)) for row in rows]

    def get_today_tasks(self) -> list[DailyTask]:
        """Get today's tasks."""
        return self.get_daily_tasks(date.today())

    def get_history(
        self,
        start_date: date = None,
        end_date: date = None,
        limit: int = 7,
    ) -> dict:
        """Get history of daily tasks."""
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=limit)

        rows = self.db.query(
            """SELECT date, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed
            FROM daily_tasks
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date DESC""",
            (start_date.isoformat(), end_date.isoformat()),
        )

        return [
            {"date": row["date"], "total": row["total"], "completed": row["completed"]}
            for row in rows
        ]
