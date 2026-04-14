"""Schedule engine with energy-aware task scheduling."""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Optional
from enum import Enum

from jarvis.utils.logger import get_logger

logger = get_logger("skills.schedule")


class TimeOfDay(str, Enum):
    MORNING = "morning"  # 6:00 - 12:00
    AFTERNOON = "afternoon"  # 12:00 - 17:00
    EVENING = "evening"  # 17:00 - 22:00
    NIGHT = "night"  # 22:00 - 6:00


@dataclass
class TimeSlot:
    """A time slot in the schedule."""

    start: datetime
    end: datetime
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    type: str = "task"  # task, break, commitment
    energy_level: Optional[int] = None
    notes: Optional[str] = None

    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)


@dataclass
class Schedule:
    """Generated daily schedule."""

    date: datetime
    slots: list[TimeSlot] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    energy_used: int = 0

    def total_focus_minutes(self) -> int:
        return sum(
            slot.duration_minutes() for slot in self.slots if slot.type == "task"
        )

    def total_breaks_minutes(self) -> int:
        return sum(
            slot.duration_minutes() for slot in self.slots if slot.type == "break"
        )


@dataclass
class Task:
    """Task for scheduling (simplified)."""

    id: str
    title: str
    energy_level: int = 5
    deadline: Optional[datetime] = None
    priority: int = 3
    status: str = "pending"


class ScheduleEngine:
    """Energy-aware task scheduler."""

    DEFAULT_WORK_START = time(9, 0)
    DEFAULT_WORK_END = time(18, 0)
    BREAK_DURATION = 5
    LONG_BREAK_DURATION = 15

    ENERGY_RECOMMENDATIONS = {
        (1, 3): {
            TimeOfDay.MORNING: 4,
            TimeOfDay.AFTERNOON: 3,
            TimeOfDay.EVENING: 3,
        },
        (4, 6): {
            TimeOfDay.MORNING: 6,
            TimeOfDay.AFTERNOON: 5,
            TimeOfDay.EVENING: 4,
        },
        (7, 10): {
            TimeOfDay.MORNING: 8,
            TimeOfDay.AFTERNOON: 7,
            TimeOfDay.EVENING: 5,
        },
    }

    def __init__(self, db=None):
        self.db = db

    def get_time_of_day(self, dt: datetime = None) -> TimeOfDay:
        """Determine time of day."""
        dt = dt or datetime.now()
        hour = dt.hour

        if 6 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 22:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT

    def get_available_energy(self, current_energy: int, time_of_day: TimeOfDay) -> int:
        """Calculate available energy for given time."""
        recommendations = self.ENERGY_RECOMMENDATIONS.get(
            self._get_energy_range(current_energy), self.ENERGY_RECOMMENDATIONS[(4, 6)]
        )
        return recommendations.get(time_of_day, current_energy)

    def _get_energy_range(self, energy: int) -> tuple:
        """Get energy range for recommendations lookup."""
        if energy <= 3:
            return (1, 3)
        elif energy <= 6:
            return (4, 6)
        else:
            return (7, 10)

    def calculate_energy_fit(self, task_energy: int, available_energy: int) -> float:
        """Calculate how well task fits available energy. Returns 0.0-1.0."""
        diff = abs(task_energy - available_energy)

        if diff <= 2:
            return 1.0
        elif diff <= 4:
            return 0.6
        elif diff <= 6:
            return 0.3
        else:
            return 0.1

    def score_task(
        self, task: Task, current_energy: int, time_of_day: TimeOfDay
    ) -> float:
        """Score task for scheduling priority."""
        available = self.get_available_energy(current_energy, time_of_day)

        energy_fit = self.calculate_energy_fit(task.energy_level, available)

        priority_score = task.priority / 5.0

        deadline_score = 0.5
        if task.deadline:
            hours_until = (task.deadline - datetime.now()).total_seconds() / 3600
            if hours_until < 0:
                deadline_score = 1.0
            elif hours_until < 24:
                deadline_score = 0.9
            elif hours_until < 72:
                deadline_score = 0.7
            elif hours_until < 168:
                deadline_score = 0.5

        final_score = priority_score * 0.4 + deadline_score * 0.3 + energy_fit * 0.3

        return final_score * 100

    def get_time_slots(
        self, work_start: time = None, work_end: time = None
    ) -> list[tuple[time, time]]:
        """Get standard work time slots."""
        start = work_start or self.DEFAULT_WORK_START
        end = work_end or self.DEFAULT_WORK_END

        slots = []
        current = datetime.combine(datetime.now().date(), start)
        end_dt = datetime.combine(datetime.now().date(), end)

        while current < end_dt:
            slot_end = current + timedelta(hours=1)
            if slot_end > end_dt:
                slot_end = end_dt
            slots.append((current, slot_end))
            current = slot_end

        return slots

    def generate_schedule(
        self,
        tasks: list[Task],
        current_energy: int = 5,
        work_start: time = None,
        work_end: time = None,
        max_hours: float = 6.0,
    ) -> Schedule:
        """Generate energy-aware schedule for tasks."""
        schedule = Schedule(date=datetime.now())

        time_of_day = self.get_time_of_day()
        available_energy = self.get_available_energy(current_energy, time_of_day)

        scored_tasks = [
            (self.score_task(t, current_energy, time_of_day), t)
            for t in tasks
            if t.status == "pending"
        ]
        scored_tasks.sort(key=lambda x: x[0], reverse=True)

        time_slots = self.get_time_slots(work_start, work_end)
        max_minutes = int(max_hours * 60)
        used_minutes = 0

        for score, task in scored_tasks:
            if used_minutes >= max_minutes:
                schedule.warnings.append(f"No more time available for '{task.title}'")
                continue

            for i, (slot_start, slot_end) in enumerate(time_slots):
                slot_minutes = int((slot_end - slot_start).total_seconds() / 60)

                energy_fit = self.calculate_energy_fit(
                    task.energy_level,
                    self.get_available_energy(
                        current_energy, self.get_time_of_day(slot_start)
                    ),
                )

                if energy_fit >= 0.3:
                    slot = TimeSlot(
                        start=slot_start,
                        end=slot_end,
                        task_id=task.id,
                        task_title=task.title,
                        type="task",
                        energy_level=task.energy_level,
                    )
                    schedule.slots.append(slot)
                    used_minutes += slot_minutes

                    if used_minutes >= max_minutes:
                        break

                    if i < len(time_slots) - 1:
                        break_start = slot_end
                        break_end = break_start + timedelta(minutes=self.BREAK_DURATION)
                        schedule.slots.append(
                            TimeSlot(
                                start=break_start,
                                end=break_end,
                                type="break",
                                notes="Short break",
                            )
                        )
                        used_minutes += self.BREAK_DURATION

                    break

        if used_minutes >= max_minutes * 0.9:
            schedule.warnings.append(
                f"Schedule is full ({used_minutes} minutes). Consider lighter tasks."
            )

        high_energy_count = sum(
            1
            for s in schedule.slots
            if s.type == "task" and s.energy_level and s.energy_level >= 7
        )
        if high_energy_count > 3:
            schedule.warnings.append(
                "Many high-energy tasks scheduled. Consider spacing them out."
            )

        return schedule

    def format_schedule(self, schedule: Schedule) -> str:
        """Format schedule as readable text."""
        lines = []
        lines.append(f"Schedule for {schedule.date.strftime('%Y-%m-%d')}")
        lines.append("=" * 50)

        for slot in schedule.slots:
            time_str = f"{slot.start.strftime('%H:%M')}-{slot.end.strftime('%H:%M')}"

            if slot.type == "break":
                lines.append(f"  {time_str} [Break] {slot.notes or 'Break'}")
            else:
                energy_icon = (
                    "[High Energy]" if slot.energy_level and slot.energy_level >= 7 else "[Low Energy]"
                )
                lines.append(f"  {time_str} {energy_icon} {slot.task_title}")

        lines.append("")
        lines.append(f"Total focus time: {schedule.total_focus_minutes()} minutes")

        if schedule.warnings:
            lines.append("\n! Warnings:")
            for warning in schedule.warnings:
                lines.append(f"  • {warning}")

        return "\n".join(lines)
