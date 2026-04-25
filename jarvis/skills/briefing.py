"""Daily briefing - morning overview of tasks and context."""

from datetime import datetime, date

from jarvis.utils.logger import get_logger

logger = get_logger("skills.briefing")


class BriefingService:
    """Generate daily briefings."""

    def __init__(self, db=None):
        self.db = db

    def generate(self, user_name: str = None) -> str:
        """Generate daily briefing."""
        from jarvis.skills.tasks import TaskService
        from jarvis.skills.schedule import ScheduleEngine, Task as ScheduleTask

        greeting = self._get_greeting()
        if user_name:
            greeting = f"Good morning, {user_name}!" if self._is_morning() else greeting

        lines = [greeting, ""]

        lines.append(self._get_date_info())
        lines.append("")

        if self.db:
            lines.append(self._get_task_summary())
            lines.append("")
            lines.append(self._get_energy_suggestion())
            lines.append("")
            lines.append(self._get_schedule_suggestion())

        return "\n".join(lines)

    def _is_morning(self) -> bool:
        """Check if it's morning."""
        return 5 <= datetime.now().hour < 12

    def _get_greeting(self) -> str:
        """Get appropriate greeting."""
        hour = datetime.now().hour

        if 5 <= hour < 12:
            return "Good morning!"
        elif 12 <= hour < 17:
            return "Good afternoon!"
        elif 17 <= hour < 22:
            return "Good evening!"
        else:
            return "Hello there!"

    def _get_date_info(self) -> str:
        """Get formatted date info."""
        today = date.today()
        weekday = today.strftime("%A")
        month_day = today.strftime("%B %d, %Y")

        return f"Today is {weekday}, {month_day}"

    def _get_task_summary(self) -> str:
        """Get task summary for the day."""
        from jarvis.skills.tasks import TaskService
        from jarvis.skills.daily_tasks import DailyTaskService
        from jarvis.db.models import TaskStatus

        task_service = TaskService(self.db)

        pending_tasks = task_service.list(status=TaskStatus.PENDING, limit=10)
        due_today = task_service.get_due_today()
        completed_today = [
            t
            for t in task_service.list(status=TaskStatus.COMPLETED, limit=100)
            if t.completed_at and t.completed_at.date() == date.today()
        ]

        lines = ["=== TODAY'S TASKS ==="]

        daily_service = DailyTaskService(self.db)
        today_daily = daily_service.get_today_tasks()

        if today_daily:
            for dt in today_daily:
                task = task_service.db.query_one(
                    "SELECT title FROM tasks WHERE id = ?", (dt.task_id,)
                )
                status_icon = "✓" if dt.status == "done" else "○"
                title = task["title"][:40] if task else "Unknown"
                lines.append(f"  {status_icon} {title}")
        else:
            lines.append("  No daily tasks set. Run 'jarvis daily generate'")

        lines.append("")

        if due_today:
            lines.append(f"  Due today: {len(due_today)}")
            for task in due_today[:3]:
                deadline_str = task.deadline.strftime("%H:%M") if task.deadline else ""
                lines.append(
                    f"      • {task.title} {f'({deadline_str})' if deadline_str else ''}"
                )
            lines.append("")

        pending = len(pending_tasks)
        lines.append(f"  Pending: {pending} task{'s' if pending != 1 else ''}")

        completed = len(completed_today)
        lines.append(f"  Completed today: {completed}")

        if pending_tasks and not due_today:
            lines.append(f"\n  Suggested focus:")
            high_priority = [t for t in pending_tasks if t.priority >= 4][:3]
            for task in high_priority:
                lines.append(f"      • {task.title} (priority: {task.priority})")

        return "\n".join(lines)

    def _get_energy_suggestion(self) -> str:
        """Get energy-based suggestion."""
        from jarvis.skills.schedule import ScheduleEngine

        engine = ScheduleEngine(self.db)
        time_of_day = engine.get_time_of_day()
        current_energy = 5

        recommendations = {
            "morning": "You're at peak focus! Great time for deep work.",
            "afternoon": "Energy is dipping. Good for routine tasks.",
            "evening": "Winding down. Consider light tasks only.",
            "night": "It's late. Maybe save tasks for tomorrow?",
        }

        suggestion = recommendations.get(time_of_day.value, "")

        return f"Energy: {suggestion}"

    def _get_schedule_suggestion(self) -> str:
        """Get schedule suggestion."""
        from jarvis.skills.tasks import TaskService
        from jarvis.skills.schedule import ScheduleEngine, Task as ScheduleTask
        from jarvis.db.models import TaskStatus

        task_service = TaskService(self.db)
        engine = ScheduleEngine(self.db)

        pending = task_service.list(status=TaskStatus.PENDING, limit=20)

        if not pending:
            return "You've completed all your tasks!"

        schedule_tasks = [
            ScheduleTask(
                id=t.id,
                title=t.title,
                energy_level=t.energy_level,
                deadline=t.deadline,
                priority=t.priority,
                status=t.status,
            )
            for t in pending
        ]

        schedule = engine.generate_schedule(schedule_tasks, max_hours=5)

        if schedule.slots:
            lines = ["Recommended Schedule:"]
            task_count = sum(1 for s in schedule.slots if s.type == "task")
            lines.append(
                f"  {task_count} tasks scheduled, {schedule.total_focus_minutes()} minutes focus time"
            )

            if schedule.warnings:
                for warning in schedule.warnings[:1]:
                    lines.append(f"  ! {warning}")

            return "\n".join(lines)

        return "No tasks scheduled. Add some tasks to get started!"

    def quick_briefing(self) -> str:
        """Generate a quick one-line briefing."""
        from jarvis.skills.tasks import TaskService
        from jarvis.db.models import TaskStatus

        if not self.db:
            return "Good morning! Ready to assist."

        task_service = TaskService(self.db)
        pending = task_service.count(TaskStatus.PENDING)
        due_today = len(task_service.get_due_today())

        greeting = self._get_greeting()

        if pending == 0:
            return f"{greeting} All tasks complete!"
        elif due_today > 0:
            return f"{greeting} You have {pending} tasks ({due_today} due today)."
        else:
            return f"{greeting} {pending} tasks pending."
