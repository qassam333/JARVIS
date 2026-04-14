"""Habits management service."""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from jarvis.utils.logger import get_logger

logger = get_logger("skills.habits")


@dataclass
class Habit:
    id: str
    name: str
    description: Optional[str]
    frequency: str
    time_of_day: str
    duration_minutes: Optional[int]
    linked_goal_id: Optional[str]
    linked_area_id: Optional[str]
    current_streak: int
    best_streak: int
    last_completed: Optional[date]
    reminder_time: Optional[str]
    is_active: bool
    created_at: Optional[datetime] = None


@dataclass
class HabitLog:
    id: str
    habit_id: str
    date: date
    completed: bool
    pages: Optional[int]
    duration_minutes: Optional[int]
    notes: Optional[str]


class HabitService:
    def __init__(self, db):
        self.db = db

    def create_habit(
        self,
        name: str,
        frequency: str = "daily",
        time_of_day: str = "evening",
        description: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        linked_goal_id: Optional[str] = None,
        linked_area_id: Optional[str] = None,
        reminder_time: Optional[str] = None,
    ) -> str:
        habit_id = str(uuid.uuid4())[:8]

        self.db.execute(
            """INSERT INTO habits 
               (id, name, description, frequency, time_of_day, duration_minutes,
                linked_goal_id, linked_area_id, reminder_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                habit_id,
                name,
                description,
                frequency,
                time_of_day,
                duration_minutes,
                linked_goal_id,
                linked_area_id,
                reminder_time,
            ),
        )

        logger.info(f"Created habit: {name} ({habit_id})")
        return habit_id

    def get_habit(self, habit_id: str) -> Optional[Habit]:
        row = self.db.query_one("SELECT * FROM habits WHERE id = ?", (habit_id,))
        if not row:
            return None

        return Habit(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            frequency=row["frequency"] or "daily",
            time_of_day=row["time_of_day"] or "evening",
            duration_minutes=row["duration_minutes"],
            linked_goal_id=row["linked_goal_id"],
            linked_area_id=row["linked_area_id"],
            current_streak=row["current_streak"] or 0,
            best_streak=row["best_streak"] or 0,
            last_completed=date.fromisoformat(row["last_completed"])
            if row["last_completed"]
            else None,
            reminder_time=row["reminder_time"],
            is_active=bool(row["is_active"]),
        )

    def get_habits(
        self, active_only: bool = True, area_id: Optional[str] = None
    ) -> list[Habit]:
        conditions = ["1=1"]
        params = []

        if active_only:
            conditions.append("is_active = 1")

        if area_id:
            conditions.append("linked_area_id = ?")
            params.append(area_id)

        where = " AND ".join(conditions)
        rows = self.db.query(
            f"SELECT * FROM habits WHERE {where} ORDER BY time_of_day, name",
            tuple(params),
        )

        return [self.get_habit(row["id"]) for row in rows]

    def update_habit(self, habit_id: str, **kwargs):
        updates = []
        params = []

        for key, value in kwargs.items():
            valid_keys = [
                "name",
                "description",
                "frequency",
                "time_of_day",
                "duration_minutes",
                "linked_goal_id",
                "linked_area_id",
                "reminder_time",
                "is_active",
            ]
            if key in valid_keys:
                updates.append(f"{key} = ?")
                params.append(value)

        if updates:
            params.append(habit_id)
            self.db.execute(
                f"UPDATE habits SET {', '.join(updates)} WHERE id = ?", tuple(params)
            )
            logger.info(f"Updated habit {habit_id}: {list(kwargs.keys())}")

    def delete_habit(self, habit_id: str):
        self.db.execute("DELETE FROM habit_logs WHERE habit_id = ?", (habit_id,))
        self.db.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        logger.info(f"Deleted habit {habit_id}")

    def log_habit(
        self,
        habit_id: str,
        log_date: Optional[date] = None,
        pages: Optional[int] = None,
        duration_minutes: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> str:
        log_date = log_date or date.today()
        log_id = str(uuid.uuid4())[:8]

        existing = self.db.query_one(
            "SELECT id FROM habit_logs WHERE habit_id = ? AND date = ?",
            (habit_id, log_date.isoformat()),
        )

        if existing:
            self.db.execute(
                """UPDATE habit_logs SET completed = 1, pages = ?, duration_minutes = ?, notes = ?
                   WHERE habit_id = ? AND date = ?""",
                (pages, duration_minutes, notes, habit_id, log_date.isoformat()),
            )
            log_id = existing["id"]
        else:
            self.db.execute(
                """INSERT INTO habit_logs (id, habit_id, date, completed, pages, duration_minutes, notes)
                   VALUES (?, ?, ?, 1, ?, ?, ?)""",
                (
                    log_id,
                    habit_id,
                    log_date.isoformat(),
                    pages,
                    duration_minutes,
                    notes,
                ),
            )

        self._update_streak(habit_id, log_date)

        logger.info(f"Logged habit {habit_id} for {log_date} (pages: {pages})")
        return log_id

    def check_habit(self, habit_id: str, log_date: Optional[date] = None) -> str:
        return self.log_habit(habit_id, log_date)

    def unlog_habit(self, habit_id: str, log_date: Optional[date] = None):
        log_date = log_date or date.today()

        self.db.execute(
            "DELETE FROM habit_logs WHERE habit_id = ? AND date = ?",
            (habit_id, log_date.isoformat()),
        )

        self._update_streak(habit_id, log_date)
        logger.info(f"Unlogged habit {habit_id} for {log_date}")

    def _update_streak(self, habit_id: str, log_date: date):
        habit = self.get_habit(habit_id)
        if not habit:
            return

        if habit.frequency == "daily":
            streak = self._calculate_daily_streak(habit_id, log_date)
        else:
            streak = self._calculate_weekly_streak(habit_id)

        best = max(habit.best_streak, streak)

        self.db.execute(
            """UPDATE habits SET current_streak = ?, best_streak = ?, last_completed = ?
               WHERE id = ?""",
            (streak, best, log_date.isoformat(), habit_id),
        )

    def _calculate_daily_streak(self, habit_id: str, from_date: date) -> int:
        streak = 0
        check_date = from_date

        while True:
            log = self.db.query_one(
                "SELECT id FROM habit_logs WHERE habit_id = ? AND date = ? AND completed = 1",
                (habit_id, check_date.isoformat()),
            )

            if log:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

            if streak > 1000:
                break

        return streak

    def _calculate_weekly_streak(self, habit_id: str) -> int:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        completed_weeks = 0
        check_week = week_start

        while True:
            week_end = check_week + timedelta(days=6)
            log = self.db.query_one(
                """SELECT id FROM habit_logs WHERE habit_id = ? 
                   AND date >= ? AND date <= ? AND completed = 1""",
                (habit_id, check_week.isoformat(), week_end.isoformat()),
            )

            if log:
                completed_weeks += 1
                check_week -= timedelta(days=7)
            else:
                break

        return completed_weeks

    def get_log(self, habit_id: str, log_date: date) -> Optional[HabitLog]:
        row = self.db.query_one(
            "SELECT * FROM habit_logs WHERE habit_id = ? AND date = ?",
            (habit_id, log_date.isoformat()),
        )

        if not row:
            return None

        return HabitLog(
            id=row["id"],
            habit_id=row["habit_id"],
            date=date.fromisoformat(row["date"]),
            completed=bool(row["completed"]),
            pages=row["pages"],
            duration_minutes=row["duration_minutes"],
            notes=row["notes"],
        )

    def get_logs(
        self,
        habit_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[HabitLog]:
        conditions = ["habit_id = ?"]
        params = [habit_id]

        if start_date:
            conditions.append("date >= ?")
            params.append(start_date.isoformat())

        if end_date:
            conditions.append("date <= ?")
            params.append(end_date.isoformat())

        where = " AND ".join(conditions)
        rows = self.db.query(
            f"SELECT * FROM habit_logs WHERE {where} ORDER BY date DESC", tuple(params)
        )

        logs = []
        for row in rows:
            logs.append(
                HabitLog(
                    id=row["id"],
                    habit_id=row["habit_id"],
                    date=date.fromisoformat(row["date"]),
                    completed=bool(row["completed"]),
                    pages=row["pages"],
                    duration_minutes=row["duration_minutes"],
                    notes=row["notes"],
                )
            )
        return logs

    def get_today_logs(self) -> list[HabitLog]:
        today = date.today().isoformat()
        rows = self.db.query(
            """SELECT hl.* FROM habit_logs hl
               JOIN habits h ON hl.habit_id = h.id
               WHERE hl.date = ? AND h.is_active = 1""",
            (today,),
        )

        logs = []
        for row in rows:
            logs.append(
                HabitLog(
                    id=row["id"],
                    habit_id=row["habit_id"],
                    date=date.fromisoformat(row["date"]),
                    completed=bool(row["completed"]),
                    pages=row["pages"],
                    duration_minutes=row["duration_minutes"],
                    notes=row["notes"],
                )
            )
        return logs

    def get_today_pending(self) -> list[Habit]:
        today = date.today()
        today_str = today.isoformat()

        rows = self.db.query(
            """SELECT h.* FROM habits h
               LEFT JOIN habit_logs hl ON h.id = hl.habit_id AND hl.date = ?
               WHERE h.is_active = 1 AND (hl.id IS NULL OR hl.completed = 0)""",
            (today_str,),
        )

        return [self.get_habit(row["id"]) for row in rows]

    def get_stats(self, habit_id: str) -> dict:
        habit = self.get_habit(habit_id)
        if not habit:
            return {}

        logs = self.get_logs(habit_id)

        total_logs = len(logs)
        total_pages = sum(log.pages or 0 for log in logs if log.pages)

        last_30_days = date.today() - timedelta(days=30)
        recent_logs = [l for l in logs if l.date >= last_30_days]
        completion_rate = len(recent_logs) / 30 * 100 if recent_logs else 0

        return {
            "habit_id": habit_id,
            "name": habit.name,
            "current_streak": habit.current_streak,
            "best_streak": habit.best_streak,
            "total_completions": total_logs,
            "total_pages": total_pages,
            "last_30_days_completion": round(completion_rate, 1),
        }

    def get_all_stats(self) -> dict:
        habits = self.get_habits()

        stats = {
            "total_habits": len(habits),
            "today_completed": len(self.get_today_logs()),
            "today_pending": len(self.get_today_pending()),
            "habits": [],
        }

        for habit in habits:
            stats["habits"].append(self.get_stats(habit.id))

        return stats

    def get_streak_warning(self) -> list[dict]:
        warnings = []
        habits = self.get_habits()
        today = date.today()

        for habit in habits:
            if habit.frequency != "daily":
                continue

            if habit.current_streak == 0:
                yesterday = today - timedelta(days=1)
                log = self.db.query_one(
                    "SELECT id FROM habit_logs WHERE habit_id = ? AND date = ? AND completed = 1",
                    (habit.id, yesterday.isoformat()),
                )

                if not log:
                    warnings.append(
                        {
                            "habit_id": habit.id,
                            "name": habit.name,
                            "streak": 0,
                            "message": f"You missed {habit.name} yesterday. Don't break the chain!",
                        }
                    )

        return warnings
