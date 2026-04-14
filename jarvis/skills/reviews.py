"""Reviews management service."""

import uuid
import json
from datetime import date, datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from jarvis.utils.logger import get_logger

logger = get_logger("skills.reviews")


@dataclass
class DailyReview:
    id: str
    date: date
    mood: Optional[int]
    energy_level: Optional[int]
    productivity_score: Optional[int]
    completed_tasks: int
    planned_tasks: int
    notes: Optional[str]
    tomorrow_plan: Optional[str]


@dataclass
class WeeklyReview:
    id: str
    week_start: date
    week_end: date
    goals_progress: dict
    completed_habits: int
    total_habits: int
    habit_completion_rate: float
    productivity_trend: Optional[str]
    mood_trend: Optional[str]
    wins: Optional[str]
    challenges: Optional[str]
    next_week_focus: Optional[str]
    grade: Optional[int]
    notes: Optional[str]


class ReviewService:
    def __init__(self, db):
        self.db = db

    def create_daily_review(
        self,
        review_date: Optional[date] = None,
        mood: Optional[int] = None,
        energy_level: Optional[int] = None,
        productivity_score: Optional[int] = None,
        completed_tasks: int = 0,
        planned_tasks: int = 0,
        notes: Optional[str] = None,
        tomorrow_plan: Optional[str] = None,
    ) -> str:
        review_date = review_date or date.today()
        review_id = str(uuid.uuid4())[:8]

        existing = self.db.query_one(
            "SELECT id FROM daily_reviews WHERE date = ?", (review_date.isoformat(),)
        )

        if existing:
            self.db.execute(
                """UPDATE daily_reviews SET 
                   mood = ?, energy_level = ?, productivity_score = ?,
                   completed_tasks = ?, planned_tasks = ?, notes = ?, tomorrow_plan = ?
                   WHERE date = ?""",
                (
                    mood,
                    energy_level,
                    productivity_score,
                    completed_tasks,
                    planned_tasks,
                    notes,
                    tomorrow_plan,
                    review_date.isoformat(),
                ),
            )
            review_id = existing["id"]
            logger.info(f"Updated daily review for {review_date}")
        else:
            self.db.execute(
                """INSERT INTO daily_reviews 
                   (id, date, mood, energy_level, productivity_score, completed_tasks, planned_tasks, notes, tomorrow_plan)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    review_id,
                    review_date.isoformat(),
                    mood,
                    energy_level,
                    productivity_score,
                    completed_tasks,
                    planned_tasks,
                    notes,
                    tomorrow_plan,
                ),
            )
            logger.info(f"Created daily review for {review_date}")

        return review_id

    def get_daily_review(self, review_date: date) -> Optional[DailyReview]:
        row = self.db.query_one(
            "SELECT * FROM daily_reviews WHERE date = ?", (review_date.isoformat(),)
        )

        if not row:
            return None

        return DailyReview(
            id=row["id"],
            date=date.fromisoformat(row["date"]),
            mood=row["mood"],
            energy_level=row["energy_level"],
            productivity_score=row["productivity_score"],
            completed_tasks=row["completed_tasks"] or 0,
            planned_tasks=row["planned_tasks"] or 0,
            notes=row["notes"],
            tomorrow_plan=row["tomorrow_plan"],
        )

    def get_recent_reviews(self, days: int = 7) -> list[DailyReview]:
        start_date = date.today() - timedelta(days=days)

        rows = self.db.query(
            "SELECT * FROM daily_reviews WHERE date >= ? ORDER BY date DESC",
            (start_date.isoformat(),),
        )

        reviews = []
        for row in rows:
            reviews.append(
                DailyReview(
                    id=row["id"],
                    date=date.fromisoformat(row["date"]),
                    mood=row["mood"],
                    energy_level=row["energy_level"],
                    productivity_score=row["productivity_score"],
                    completed_tasks=row["completed_tasks"] or 0,
                    planned_tasks=row["planned_tasks"] or 0,
                    notes=row["notes"],
                    tomorrow_plan=row["tomorrow_plan"],
                )
            )
        return reviews

    def create_weekly_review(
        self,
        week_start: Optional[date] = None,
        week_end: Optional[date] = None,
        goals_progress: Optional[dict] = None,
        completed_habits: int = 0,
        total_habits: int = 0,
        productivity_trend: Optional[str] = None,
        mood_trend: Optional[str] = None,
        wins: Optional[str] = None,
        challenges: Optional[str] = None,
        next_week_focus: Optional[str] = None,
        grade: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> str:
        if not week_end:
            week_end = week_start + timedelta(days=6) if week_start else date.today()
        if not week_start:
            week_start = week_end - timedelta(days=6)

        review_id = str(uuid.uuid4())[:8]

        existing = self.db.query_one(
            "SELECT id FROM weekly_reviews WHERE week_start = ?",
            (week_start.isoformat(),),
        )

        completion_rate = (
            (completed_habits / total_habits * 100) if total_habits > 0 else 0
        )

        if existing:
            self.db.execute(
                """UPDATE weekly_reviews SET 
                   week_end = ?, goals_progress = ?, completed_habits = ?, total_habits = ?,
                   habit_completion_rate = ?, productivity_trend = ?, mood_trend = ?,
                   wins = ?, challenges = ?, next_week_focus = ?, grade = ?, notes = ?
                   WHERE week_start = ?""",
                (
                    week_end.isoformat(),
                    json.dumps(goals_progress or {}),
                    completed_habits,
                    total_habits,
                    completion_rate,
                    productivity_trend,
                    mood_trend,
                    wins,
                    challenges,
                    next_week_focus,
                    grade,
                    notes,
                    week_start.isoformat(),
                ),
            )
            review_id = existing["id"]
        else:
            self.db.execute(
                """INSERT INTO weekly_reviews 
                   (id, week_start, week_end, goals_progress, completed_habits, total_habits,
                    habit_completion_rate, productivity_trend, mood_trend, wins, challenges,
                    next_week_focus, grade, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    review_id,
                    week_start.isoformat(),
                    week_end.isoformat(),
                    json.dumps(goals_progress or {}),
                    completed_habits,
                    total_habits,
                    completion_rate,
                    productivity_trend,
                    mood_trend,
                    wins,
                    challenges,
                    next_week_focus,
                    grade,
                    notes,
                ),
            )

        logger.info(f"Created weekly review for week of {week_start}")
        return review_id

    def get_weekly_review(self, week_start: date) -> Optional[WeeklyReview]:
        row = self.db.query_one(
            "SELECT * FROM weekly_reviews WHERE week_start = ?",
            (week_start.isoformat(),),
        )

        if not row:
            return None

        return WeeklyReview(
            id=row["id"],
            week_start=date.fromisoformat(row["week_start"]),
            week_end=date.fromisoformat(row["week_end"]),
            goals_progress=json.loads(row["goals_progress"] or "{}"),
            completed_habits=row["completed_habits"] or 0,
            total_habits=row["total_habits"] or 0,
            habit_completion_rate=row["habit_completion_rate"] or 0,
            productivity_trend=row["productivity_trend"],
            mood_trend=row["mood_trend"],
            wins=row["wins"],
            challenges=row["challenges"],
            next_week_focus=row["next_week_focus"],
            grade=row["grade"],
            notes=row["notes"],
        )

    def get_recent_weekly_reviews(self, weeks: int = 4) -> list[WeeklyReview]:
        reviews = []
        for i in range(weeks):
            week_end = date.today() - timedelta(days=date.today().weekday() + (7 * i))
            week_start = week_end - timedelta(days=6)
            review = self.get_weekly_review(week_start)
            if review:
                reviews.append(review)
        return reviews

    def generate_weekly_summary(self) -> dict:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        daily_reviews = self.get_recent_reviews(7)

        total_mood = sum(r.mood or 0 for r in daily_reviews if r.mood)
        total_energy = sum(r.energy_level or 0 for r in daily_reviews if r.energy_level)
        total_productivity = sum(
            r.productivity_score or 0 for r in daily_reviews if r.productivity_score
        )

        count_with_mood = sum(1 for r in daily_reviews if r.mood)
        count_with_energy = sum(1 for r in daily_reviews if r.energy_level)
        count_with_productivity = sum(1 for r in daily_reviews if r.productivity_score)

        return {
            "week_start": week_start,
            "week_end": week_end,
            "days_reviewed": len(daily_reviews),
            "avg_mood": round(total_mood / count_with_mood, 1)
            if count_with_mood > 0
            else None,
            "avg_energy": round(total_energy / count_with_energy, 1)
            if count_with_energy > 0
            else None,
            "avg_productivity": round(total_productivity / count_with_productivity, 1)
            if count_with_productivity > 0
            else None,
            "daily_reviews": [
                {
                    "date": r.date.isoformat(),
                    "mood": r.mood,
                    "energy": r.energy_level,
                    "productivity": r.productivity_score,
                    "completed": r.completed_tasks,
                    "planned": r.planned_tasks,
                }
                for r in daily_reviews
            ],
        }

    def get_this_week_stats(self) -> dict:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        habit_logs = self.db.query(
            """SELECT hl.*, h.name, h.frequency 
               FROM habit_logs hl
               JOIN habits h ON hl.habit_id = h.id
               WHERE hl.date >= ? AND hl.completed = 1""",
            (week_start.isoformat(),),
        )

        all_habits = self.db.query(
            "SELECT id, name, frequency FROM habits WHERE is_active = 1"
        )

        days_in_week = (today - week_start).days + 1
        expected_logs = len(all_habits) * days_in_week

        return {
            "week_start": week_start,
            "habits_completed": len(habit_logs),
            "habits_expected": expected_logs,
            "completion_rate": round(len(habit_logs) / expected_logs * 100, 1)
            if expected_logs > 0
            else 0,
            "habits_tracked": len(all_habits),
        }
