"""Accountability engine with strict but motivational messaging."""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from jarvis.utils.logger import get_logger

logger = get_logger("skills.accountability")


class AccountabilityEngine:
    def __init__(
        self, db, profile_service, goal_service, habit_service, review_service
    ):
        self.db = db
        self.profile = profile_service
        self.goals = goal_service
        self.habits = habit_service
        self.reviews = review_service

    def _get_dream_project(self) -> str:
        """Get the user's top active goal name for motivational messaging."""
        try:
            active = self.goals.get_goals(parent_only=True, status="active")
            if active:
                return active[0].title
        except Exception:
            pass
        return "your goals"

    def get_today_preview(self) -> str:
        profile = self.profile.get_profile()
        today = date.today()

        day_name = today.strftime("%A")
        is_grad_day = day_name.lower() in ["saturday", "sunday", "monday"]

        pending_habits = self.habits.get_today_pending()
        upcoming_goals = self.goals.get_upcoming(days=7)

        lines = []
        lines.append(f"Today is {day_name}, {today.strftime('%B %d, %Y')}")

        if is_grad_day:
            lines.append("Grad project day - 3-5hr session expected")

        lines.append("")

        if pending_habits:
            lines.append("Today's habits:")
            for h in pending_habits[:5]:
                lines.append(f"  - {h.name}")

        if upcoming_goals:
            lines.append("")
            lines.append("Upcoming deadlines:")
            for g in upcoming_goals[:3]:
                if g.target_date:
                    days = (g.target_date - today).days
                    lines.append(f"  - {g.title}: {days} days left")

        return "\n".join(lines)

    def get_morning_message(self) -> str:
        today = date.today()
        day_name = today.strftime("%A")

        pending = self.habits.get_today_pending()
        upcoming = self.goals.get_upcoming(days=7)

        lines = [
            f"Good morning. Today is {day_name}.",
            "",
        ]

        if pending:
            lines.append("Your habits for today:")
            for h in pending:
                lines.append(f"  - {h.name}")

        lines.append("")
        dream = self._get_dream_project()
        lines.append(f"Stay focused. {dream} needs the work you do today.")

        return "\n".join(lines)

    def get_evening_check(self) -> str:
        today = date.today()
        today_logs = self.habits.get_today_logs()
        pending = self.habits.get_today_pending()

        lines = [
            "Day review:",
            "",
        ]

        completed = len(today_logs)
        total = completed + len(pending)

        if total > 0:
            pct = int((completed / total) * 100)
            lines.append(f"Habits: {completed}/{total} ({pct}%)")

        for log in today_logs[:3]:
            habit = self.habits.get_habit(log.habit_id)
            if habit:
                extra = f" ({log.pages} pages)" if log.pages else ""
                extra += f" - {log.duration_minutes}min" if log.duration_minutes else ""
                lines.append(f"  - {habit.name}{extra}")

        if pending:
            lines.append("")
            lines.append("Missed:")
            for h in pending:
                lines.append(f"  - {h.name}")

        lines.append("")
        dream = self._get_dream_project()
        lines.append(f"Rest well. Tomorrow is another day to build {dream}.")

        return "\n".join(lines)

    def get_habit_streak_message(self, habit_id: str) -> str:
        habit = self.habits.get_habit(habit_id)
        if not habit:
            return ""

        stats = self.habits.get_stats(habit_id)

        lines = []
        if habit.current_streak >= 7:
            lines.append(f"Fire emoji 7 day streak - {habit.name}!")
            lines.append("")
            lines.append(f"You're building momentum. Keep this pace and")
            lines.append(f"the goal is getting closer every day.")
            lines.append("")
            lines.append(f"Keep going. {self._get_dream_project()} is becoming real.")
        elif habit.current_streak >= 3:
            lines.append(f"3+ day streak on {habit.name}!")
            lines.append("You're building a habit. Consistency is key.")
        else:
            lines.append(f"Streak: {habit.current_streak} days")
            lines.append("Keep building that streak!")

        return "\n".join(lines)

    def get_habit_missed_message(self, habit_id: str) -> str:
        habit = self.habits.get_habit(habit_id)
        if not habit:
            return ""

        lines = [
            f"You've skipped {habit.name}.",
            "",
        ]

        if habit.linked_goal_id:
            goal = self.goals.get_goal(habit.linked_goal_id)
            if goal:
                lines.append(f"This is tied to: {goal.title}")
                if goal.target_date:
                    days = (goal.target_date - date.today()).days
                    if days > 0:
                        lines.append(f"{days} days until deadline.")

        lines.append("")
        lines.append("Reality check:")
        lines.append(
            "Missing days adds up. Every skipped session is progress you don't make."
        )
        lines.append("")
        lines.append("Options:")
        lines.append("  [1] Do a quick session now to compensate")
        lines.append("  [2] Reschedule for tomorrow")
        lines.append("  [3] Be honest - is this goal still important?")

        return "\n".join(lines)

    def get_weekly_review_message(self) -> str:
        summary = self.reviews.generate_weekly_summary()
        stats = self.reviews.get_this_week_stats()

        today = date.today()
        week_end = today

        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        lines = [
            f"Week {stats['week_start'].strftime('%W')} Summary:",
            "=" * 40,
            "",
            "COMPLETED:",
        ]

        for habit_stat in stats.get("habits", [])[:5]:
            name = habit_stat.get("name", "Unknown")
            streak = habit_stat.get("current_streak", 0)
            lines.append(f"  - {name}: {streak} day streak")

        lines.append("")
        lines.append(
            f"HABITS: {stats['completed_habits']}/{stats['habits_expected']} ({stats['completion_rate']}%)"
        )

        if summary.get("avg_productivity"):
            lines.append(f"AVG PRODUCTIVITY: {summary['avg_productivity']}/10")

        lines.append("")
        lines.append(f"Keep pushing. Every day is a step toward {self._get_dream_project()}.")

        return "\n".join(lines)

    def get_overdue_warning(self) -> list[str]:
        messages = []
        overdue = self.goals.get_overdue()

        for goal in overdue:
            if goal.target_date:
                days = (date.today() - goal.target_date).days

                lines = [
                    f"Overdue: {goal.title}",
                    f"Was due {days} days ago",
                    "",
                ]

                if goal.progress > 0:
                    lines.append(f"Progress: {goal.progress}%")

                lines.append("Don't let this slide. Update or close this goal.")
                messages.append("\n".join(lines))

        return messages

    def get_deadline_approaching(self) -> list[str]:
        messages = []
        upcoming = self.goals.get_upcoming(days=14)

        for goal in upcoming:
            if goal.target_date:
                days = (goal.target_date - date.today()).days

                if days <= 7:
                    lines = [
                        f"ALERT: {goal.title}",
                        f"Due in {days} days",
                        f"Progress: {goal.progress}%",
                        "",
                    ]

                    if goal.progress < 50:
                        lines.append("You're behind. Time to focus.")
                    elif goal.progress < 80:
                        lines.append("Almost there. Push through.")
                    else:
                        lines.append("Final stretch. You got this.")

                    messages.append("\n".join(lines))

        return messages

    def get_graduation_countdown(self) -> str:
        profile = self.profile.get_profile()

        if not profile.grad_deadline:
            return ""

        days = (profile.grad_deadline - date.today()).days

        lines = [
            f"Countdown to graduation: {days} days",
            "",
        ]

        if days <= 30:
            lines.append("Critical period. Every day counts.")
            lines.append("Grad project takes priority.")
        elif days <= 60:
            lines.append("Two months left. Stay focused.")
        elif days <= 90:
            lines.append("Three months. Time to accelerate.")

        return "\n".join(lines)

    def get_motivation_message(self) -> str:
        dream = self._get_dream_project()

        messages = [
            f"Every line of code brings {dream} closer to reality.",
            "The grind today builds the future tomorrow.",
            "No one else is going to build your dreams for you.",
            "Your future self will thank you for the work you do now.",
            f"{dream} won't finish itself. Get to it.",
            "Discipline beats motivation. Keep showing up.",
            "The only way out is through. Keep pushing.",
            f"Stay focused. Stay disciplined. Ship {dream}.",
        ]

        import random

        return random.choice(messages)

    def log_accountability(
        self, trigger: str, message: str, action: Optional[str] = None
    ):
        log_id = str(uuid.uuid4())[:8]

        self.db.execute(
            """INSERT INTO accountability_log (id, type, trigger, message, action_taken)
               VALUES (?, ?, ?, ?, ?)""",
            (log_id, "reminder", trigger, message, action),
        )
