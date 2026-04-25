"""Goals management service."""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from jarvis.utils.logger import get_logger

logger = get_logger("skills.goals")


@dataclass
class Goal:
    id: str
    title: str
    description: Optional[str]
    area_id: Optional[str]
    parent_goal_id: Optional[str]
    target_date: Optional[date]
    start_date: Optional[date]
    progress: int
    priority: str
    status: str
    is_milestone: bool
    created_at: datetime


@dataclass
class Milestone:
    id: str
    goal_id: str
    title: str
    target_date: Optional[date]
    progress: int
    completed: bool
    completed_at: Optional[datetime]
    order_index: int


class GoalService:
    def __init__(self, db):
        self.db = db

    def create_goal(
        self,
        title: str,
        area_id: Optional[str] = None,
        description: Optional[str] = None,
        parent_goal_id: Optional[str] = None,
        target_date: Optional[date] = None,
        start_date: Optional[date] = None,
        priority: str = "medium",
    ) -> str:
        goal_id = str(uuid.uuid4())[:8]

        self.db.execute(
            """INSERT INTO goals 
               (id, title, description, area_id, parent_goal_id, target_date, start_date, priority)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                goal_id,
                title,
                description,
                area_id,
                parent_goal_id,
                target_date.isoformat() if target_date else None,
                start_date.isoformat() if start_date else None,
                priority,
            ),
        )

        logger.info(f"Created goal: {title} ({goal_id})")
        return goal_id

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        row = self.db.query_one("SELECT * FROM goals WHERE id = ?", (goal_id,))
        if not row:
            return None

        return Goal(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            area_id=row["area_id"],
            parent_goal_id=row["parent_goal_id"],
            target_date=date.fromisoformat(row["target_date"])
            if row["target_date"]
            else None,
            start_date=date.fromisoformat(row["start_date"])
            if row["start_date"]
            else None,
            progress=row["progress"] or 0,
            priority=row["priority"] or "medium",
            status=row["status"] or "active",
            is_milestone=bool(row["is_milestone"]),
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else datetime.now(),
        )

    def get_goals(
        self,
        area_id: Optional[str] = None,
        status: Optional[str] = None,
        parent_only: bool = False,
    ) -> list[Goal]:
        conditions = ["1=1"]
        params = []

        if area_id:
            conditions.append("area_id = ?")
            params.append(area_id)

        if status:
            conditions.append("status = ?")
            params.append(status)

        if parent_only:
            conditions.append("parent_goal_id IS NULL")
            conditions.append("is_milestone = 0")

        where = " AND ".join(conditions)
        rows = self.db.query(
            f"SELECT * FROM goals WHERE {where} ORDER BY target_date ASC, priority DESC",
            tuple(params),
        )

        return [self.get_goal(row["id"]) for row in rows]

    def get_child_goals(self, parent_id: str) -> list[Goal]:
        rows = self.db.query(
            "SELECT * FROM goals WHERE parent_goal_id = ? ORDER BY created_at",
            (parent_id,),
        )
        return [self.get_goal(row["id"]) for row in rows]

    def update_goal(self, goal_id: str, **kwargs):
        updates = []
        params = []

        for key, value in kwargs.items():
            if key == "target_date" and value:
                value = value.isoformat()
            elif key == "start_date" and value:
                value = value.isoformat()

            valid_keys = [
                "title",
                "description",
                "area_id",
                "parent_goal_id",
                "target_date",
                "start_date",
                "progress",
                "priority",
                "status",
            ]
            if key in valid_keys and value is not None:
                updates.append(f"{key} = ?")
                params.append(value)

        if updates:
            params.append(goal_id)
            self.db.execute(
                f"UPDATE goals SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                tuple(params),
            )
            logger.info(f"Updated goal {goal_id}: {list(kwargs.keys())}")

    def update_progress(self, goal_id: str, progress: int):
        progress = max(0, min(100, progress))
        self.update_goal(goal_id, progress=progress)

        if progress >= 100:
            self.update_goal(goal_id, status="completed")
            self._complete_milestones(goal_id)

    def delete_goal(self, goal_id: str):
        self.db.execute("DELETE FROM milestones WHERE goal_id = ?", (goal_id,))
        self.db.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        logger.info(f"Deleted goal {goal_id}")

    def add_milestone(
        self,
        goal_id: str,
        title: str,
        target_date: Optional[date] = None,
        order_index: int = 0,
    ) -> str:
        milestone_id = str(uuid.uuid4())[:8]

        self.db.execute(
            """INSERT INTO milestones (id, goal_id, title, target_date, order_index)
               VALUES (?, ?, ?, ?, ?)""",
            (
                milestone_id,
                goal_id,
                title,
                target_date.isoformat() if target_date else None,
                order_index,
            ),
        )

        logger.info(f"Added milestone: {title} to goal {goal_id}")
        return milestone_id

    def get_milestones(self, goal_id: str) -> list[Milestone]:
        rows = self.db.query(
            "SELECT * FROM milestones WHERE goal_id = ? ORDER BY order_index",
            (goal_id,),
        )

        milestones = []
        for row in rows:
            milestones.append(
                Milestone(
                    id=row["id"],
                    goal_id=row["goal_id"],
                    title=row["title"],
                    target_date=date.fromisoformat(row["target_date"])
                    if row["target_date"]
                    else None,
                    progress=row["progress"] or 0,
                    completed=bool(row["completed"]),
                    completed_at=datetime.fromisoformat(row["completed_at"])
                    if row["completed_at"]
                    else None,
                    order_index=row["order_index"] or 0,
                )
            )
        return milestones

    def update_milestone(self, milestone_id: str, **kwargs):
        updates = []
        params = []

        for key, value in kwargs.items():
            if key == "target_date" and value:
                value = value.isoformat()

            valid_keys = [
                "title",
                "target_date",
                "progress",
                "completed",
                "order_index",
            ]
            if key in valid_keys and value is not None:
                updates.append(f"{key} = ?")
                params.append(value)

        if kwargs.get("completed") and not kwargs.get("completed_at"):
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())

        if updates:
            params.append(milestone_id)
            self.db.execute(
                f"UPDATE milestones SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )

    def complete_milestone(self, milestone_id: str):
        self.update_milestone(milestone_id, completed=True, progress=100)

        row = self.db.query_one(
            "SELECT goal_id FROM milestones WHERE id = ?", (milestone_id,)
        )
        if row:
            self._update_goal_from_milestones(row["goal_id"])

    def _update_goal_from_milestones(self, goal_id: str):
        milestones = self.get_milestones(goal_id)
        if not milestones:
            return

        completed = sum(1 for m in milestones if m.completed)
        progress = int((completed / len(milestones)) * 100)

        self.update_goal(goal_id, progress=progress)

        if progress >= 100:
            self.update_goal(goal_id, status="completed")

    def _complete_milestones(self, goal_id: str):
        for milestone in self.get_milestones(goal_id):
            if not milestone.completed:
                self.complete_milestone(milestone.id)

    def get_upcoming(self, days: int = 7) -> list[Goal]:
        target_date = date.today()
        end_date = target_date + timedelta(days=days)

        rows = self.db.query(
            """SELECT * FROM goals 
               WHERE target_date IS NOT NULL 
               AND target_date <= ? 
               AND target_date >= ?
               AND status = 'active'
               ORDER BY target_date""",
            (end_date.isoformat(), target_date.isoformat()),
        )

        return [self.get_goal(row["id"]) for row in rows]

    def get_overdue(self) -> list[Goal]:
        today = date.today().isoformat()
        rows = self.db.query(
            """SELECT * FROM goals 
               WHERE target_date < ?
               AND status = 'active'
               ORDER BY target_date""",
            (today,),
        )
        return [self.get_goal(row["id"]) for row in rows]

    def get_progress_summary(self) -> dict:
        total = self.db.query_one(
            "SELECT COUNT(*) as count FROM goals WHERE is_milestone = 0"
        )
        active = self.db.query_one(
            "SELECT COUNT(*) as count FROM goals WHERE status = 'active' AND is_milestone = 0"
        )
        completed = self.db.query_one(
            "SELECT COUNT(*) as count FROM goals WHERE status = 'completed' AND is_milestone = 0"
        )

        return {
            "total": total["count"] if total else 0,
            "active": active["count"] if active else 0,
            "completed": completed["count"] if completed else 0,
        }

    def generate_tasks(self, goal_id: str) -> list[str]:
        """Generate actionable tasks for a goal.

        Breaks down a goal into achievable tasks and adds them to the task list.
        """
        goal = self.get_goal(goal_id)
        if not goal:
            return []

        from jarvis.skills.tasks import TaskService

        task_service = TaskService(self.db)
        task_ids = []

        priority_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        energy_map = {"low": 3, "medium": 5, "high": 7, "critical": 8}
        priority = priority_map.get(goal.priority, 2)
        energy = energy_map.get(goal.priority, 5)

        task_templates = self._get_task_templates(goal)
        for i, template in enumerate(task_templates):
            task_title = f"{goal.title}: {template['title']}"
            task_desc = template.get("description", "")

            from jarvis.db.models import TaskCreate, TaskSource

            task_data = TaskCreate(
                title=task_title,
                description=task_desc,
                energy_level=energy,
                deadline=template.get("deadline"),
                priority=priority,
                tags=[goal.area_id] if goal.area_id else [],
                source=TaskSource.MANUAL,
            )

            task = task_service.create(task_data)
            task_ids.append(task.id)

            self.db.execute(
                "UPDATE tasks SET goal_id = ? WHERE id = ?",
                (goal_id, task.id),
            )

            logger.info(f"Generated task: {task_title} for goal {goal_id}")

        return task_ids

    def _get_task_templates(self, goal: Goal) -> list[dict]:
        """Get task templates based on goal properties."""
        from datetime import datetime, timedelta

        templates = []
        today = datetime.now().date()

        if goal.area_id == "career":
            templates = self._career_goal_tasks(goal, today)
        elif goal.area_id == "projects":
            templates = self._project_goal_tasks(goal, today)
        elif goal.area_id == "learning":
            templates = self._learning_goal_tasks(goal, today)
        elif goal.area_id == "religion":
            templates = self._religion_goal_tasks(goal, today)
        else:
            templates = self._generic_goal_tasks(goal, today)

        return templates

    def _career_goal_tasks(self, goal: Goal, today) -> list[dict]:
        """Generate tasks for career goals."""
        templates = []

        if "graduation" in goal.title.lower():
            templates = [
                {
                    "title": "Define project scope",
                    "deadline": today + timedelta(days=7),
                },
                {
                    "title": "Research existing solutions",
                    "deadline": today + timedelta(days=14),
                },
                {
                    "title": "Create project plan",
                    "deadline": today + timedelta(days=21),
                },
                {
                    "title": "Set up development environment",
                    "deadline": today + timedelta(days=28),
                },
                {
                    "title": "Implement core features",
                    "deadline": today + timedelta(days=60),
                },
                {
                    "title": "Write documentation",
                    "deadline": today + timedelta(days=75),
                },
                {"title": "Test and fix bugs", "deadline": today + timedelta(days=90)},
                {"title": "Submit final project", "deadline": goal.target_date},
            ]
        elif "ue5" in goal.title.lower() or "unreal" in goal.title.lower():
            templates = [
                {
                    "title": "Complete UE5 fundamentals course",
                    "deadline": today + timedelta(days=14),
                },
                {
                    "title": "Build first demo scene",
                    "deadline": today + timedelta(days=21),
                },
                {
                    "title": "Learn Blueprints basics",
                    "deadline": today + timedelta(days=30),
                },
                {
                    "title": "Create particle effects",
                    "deadline": today + timedelta(days=45),
                },
                {"title": "Implement basic AI", "deadline": today + timedelta(days=60)},
                {"title": "Build portfolio project", "deadline": goal.target_date},
            ]
        elif "job" in goal.title.lower():
            templates = [
                {"title": "Update CV/Resume", "deadline": today + timedelta(days=3)},
                {
                    "title": "Create LinkedIn profile",
                    "deadline": today + timedelta(days=5),
                },
                {
                    "title": "Build portfolio website",
                    "deadline": today + timedelta(days=14),
                },
                {"title": "Research companies", "deadline": today + timedelta(days=21)},
                {"title": "Apply to 5 jobs", "deadline": today + timedelta(days=30)},
                {
                    "title": "Prepare for interviews",
                    "deadline": today + timedelta(days=45),
                },
                {
                    "title": "Network on LinkedIn",
                    "deadline": today + timedelta(days=60),
                },
            ]
        elif "portfolio" in goal.title.lower():
            templates = [
                {
                    "title": "Choose projects to showcase",
                    "deadline": today + timedelta(days=3),
                },
                {
                    "title": "Record walkthrough videos",
                    "deadline": today + timedelta(days=7),
                },
                {"title": "Write case studies", "deadline": today + timedelta(days=14)},
                {
                    "title": "Design portfolio layout",
                    "deadline": today + timedelta(days=21),
                },
                {"title": "Build website", "deadline": today + timedelta(days=30)},
                {"title": "Deploy and test", "deadline": goal.target_date},
            ]
        else:
            templates = self._generic_goal_tasks(goal, today)

        return templates

    def _project_goal_tasks(self, goal: Goal, today) -> list[dict]:
        """Generate tasks for project goals."""
        templates = []

        if "linkit" in goal.title.lower():
            templates = [
                {
                    "title": "Review current build",
                    "deadline": today + timedelta(days=3),
                },
                {"title": "Fix critical bugs", "deadline": today + timedelta(days=7)},
                {"title": "Improve graphics", "deadline": today + timedelta(days=14)},
                {"title": "Add new features", "deadline": today + timedelta(days=21)},
                {
                    "title": "Playtest and balance",
                    "deadline": today + timedelta(days=30),
                },
                {"title": "Polish UI/UX", "deadline": today + timedelta(days=45)},
                {"title": "Build release version", "deadline": goal.target_date},
            ]
        elif "mansaf" in goal.title.lower() or "legendary" in goal.title.lower():
            templates = [
                {
                    "title": "Write game design doc",
                    "deadline": today + timedelta(days=7),
                },
                {"title": "Create prototype", "deadline": today + timedelta(days=21)},
                {
                    "title": "Implement core mechanics",
                    "deadline": today + timedelta(days=60),
                },
                {"title": "Build level design", "deadline": today + timedelta(days=90)},
                {"title": "Add content", "deadline": today + timedelta(days=120)},
                {"title": "QA and testing", "deadline": today + timedelta(days=150)},
                {"title": "Marketing", "deadline": goal.target_date},
            ]
        elif "afterfall" in goal.title.lower():
            templates = [
                {"title": "Research AAA games", "deadline": today + timedelta(days=14)},
                {
                    "title": "Define project scope",
                    "deadline": today + timedelta(days=30),
                },
                {"title": "Learn advanced UE5", "deadline": today + timedelta(days=60)},
                {
                    "title": "Build vertical slice",
                    "deadline": today + timedelta(days=90),
                },
                {
                    "title": "Create vertical slice",
                    "deadline": today + timedelta(days=180),
                },
                {"title": "Full production", "deadline": goal.target_date},
            ]
        else:
            templates = self._generic_goal_tasks(goal, today)

        return templates

    def _learning_goal_tasks(self, goal: Goal, today) -> list[dict]:
        """Generate tasks for learning goals."""
        templates = []

        if "python" in goal.title.lower():
            templates = [
                {
                    "title": "Complete Python basics",
                    "deadline": today + timedelta(days=7),
                },
                {"title": "Learn OOP concepts", "deadline": today + timedelta(days=14)},
                {
                    "title": "Practice data structures",
                    "deadline": today + timedelta(days=21),
                },
                {
                    "title": "Build small projects",
                    "deadline": today + timedelta(days=30),
                },
                {"title": "Learn testing", "deadline": today + timedelta(days=45)},
                {"title": "Contribute to open source", "deadline": goal.target_date},
            ]
        elif "english" in goal.title.lower() or "fluency" in goal.title.lower():
            templates = [
                {
                    "title": "Practice speaking daily",
                    "deadline": today + timedelta(days=1),
                },
                {
                    "title": "Watch English content",
                    "deadline": today + timedelta(days=7),
                },
                {"title": "Write 500 words", "deadline": today + timedelta(days=14)},
                {"title": "Take proficiency test", "deadline": goal.target_date},
            ]
        elif "third language" in goal.title.lower():
            templates = [
                {"title": "Choose language", "deadline": today + timedelta(days=3)},
                {"title": "Learn basics (A1)", "deadline": today + timedelta(days=30)},
                {"title": "Intermediate (A2)", "deadline": today + timedelta(days=60)},
                {"title": "Upper intermediate (B1)", "deadline": goal.target_date},
            ]
        elif "it" in goal.title.lower() or "cloud" in goal.title.lower():
            templates = [
                {
                    "title": "Take cloud fundamentals course",
                    "deadline": today + timedelta(days=14),
                },
                {
                    "title": "Complete security basics",
                    "deadline": today + timedelta(days=30),
                },
                {"title": "Learn networking", "deadline": today + timedelta(days=45)},
                {"title": "Get certification", "deadline": goal.target_date},
            ]
        else:
            templates = self._generic_goal_tasks(goal, today)

        return templates

    def _religion_goal_tasks(self, goal: Goal, today) -> list[dict]:
        """Generate tasks for religion goals."""
        return [
            {"title": "Daily practice", "deadline": today + timedelta(days=1)},
            {
                "title": "Track progress for 7 days",
                "deadline": today + timedelta(days=7),
            },
            {
                "title": "Track progress for 30 days",
                "deadline": today + timedelta(days=30),
            },
        ]

    def _generic_goal_tasks(self, goal: Goal, today) -> list[dict]:
        """Generate generic tasks for any goal."""
        target = goal.target_date or (today + timedelta(days=30))
        days_until = (target - today).days

        num_tasks = max(3, min(7, days_until // 10))
        interval = days_until // num_tasks if num_tasks > 0 else 1

        templates = []
        for i in range(num_tasks):
            templates.append(
                {
                    "title": f"Phase {i + 1}",
                    "deadline": today + timedelta(days=(i + 1) * interval),
                }
            )

        templates.append(
            {
                "title": "Final review",
                "deadline": target,
            }
        )

        return templates
