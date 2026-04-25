"""Handlers for habit, goal, and energy voice/NLU commands."""

from jarvis.core.intent_parser import Intent
from jarvis.core.brain import Response, Context
from jarvis.utils.logger import get_logger

logger = get_logger("core.habit_handlers")


def handle_log_habit(intent: Intent, context: Context) -> Response:
    """Handle log habit intent.
    
    Matches the habit name from intent entities against existing habits
    using fuzzy string matching, then logs today's entry.
    """
    if not context.db:
        return Response(success=False, message="Database not available")

    from jarvis.skills.habits import HabitService
    from difflib import SequenceMatcher

    content = intent.entities.get("content", "") or intent.entities.get("title", "")
    if not content:
        return Response(success=False, message="Which habit did you complete? Try 'log exercise'.")

    service = HabitService(context.db)
    habits = service.get_habits()

    if not habits:
        return Response(
            success=True,
            message="You don't have any habits set up yet. Use the CLI to add one: jarvis habit add <name>",
        )

    # Find best matching habit by name
    best_match = None
    best_score = 0.0

    # Clean the content — remove common filler words
    clean_content = content.lower().strip()
    for filler in ["my", "the", "a", "an", "today", "habit", "log", "track", "did", "done"]:
        clean_content = clean_content.replace(filler, "").strip()

    for habit in habits:
        habit_name = habit.name.lower()
        
        # Direct substring match
        if clean_content in habit_name or habit_name in clean_content:
            best_match = habit
            best_score = 1.0
            break

        # Fuzzy match
        score = SequenceMatcher(None, clean_content, habit_name).ratio()
        if score > best_score:
            best_score = score
            best_match = habit

    if best_match and best_score > 0.4:
        service.log_habit(best_match.id)
        updated = service.get_habit(best_match.id)
        streak = updated.current_streak if updated else 0
        return Response(
            success=True,
            message=f"Logged '{best_match.name}'. Streak: {streak} day{'s' if streak != 1 else ''}!",
            data={"habit_id": best_match.id, "name": best_match.name, "streak": streak},
        )
    else:
        habit_names = ", ".join(h.name for h in habits[:5])
        return Response(
            success=False,
            message=f"Couldn't find a habit matching '{content}'. Your habits: {habit_names}",
        )


def handle_list_habits(intent: Intent, context: Context) -> Response:
    """Handle list habits intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    from jarvis.skills.habits import HabitService
    from datetime import date

    service = HabitService(context.db)
    habits = service.get_habits()

    if not habits:
        return Response(
            success=True,
            message="No habits tracked yet. Add one with: jarvis habit add <name>",
        )

    today_logs = {log.habit_id: log for log in service.get_today_logs()}

    lines = [f"You have {len(habits)} habits:\n"]
    for habit in habits:
        done = habit.id in today_logs
        icon = "done" if done else "pending"
        streak_text = f"(streak: {habit.current_streak})" if habit.current_streak > 0 else ""
        lines.append(f"  [{icon}] {habit.name} {streak_text}")

    # Streak warnings
    warnings = service.get_streak_warning()
    if warnings:
        lines.append("\nWarnings:")
        for w in warnings[:3]:
            lines.append(f"  ! {w['message']}")

    habit_data = [
        {"id": h.id, "title": h.name, "streak": h.current_streak, "done": h.id in today_logs}
        for h in habits
    ]

    return Response(
        success=True,
        message="\n".join(lines),
        data=habit_data,
    )


def handle_goal_status(intent: Intent, context: Context) -> Response:
    """Handle goal status intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    from jarvis.skills.goals import GoalService

    service = GoalService(context.db)

    # Check if asking about specific goal
    content = intent.entities.get("content", "")

    if content and content not in ("goals", "goal", "progress", "status"):
        # Try to find specific goal
        goals = service.get_goals(parent_only=True)
        for goal in goals:
            if content.lower() in goal.title.lower():
                milestones = service.get_milestones(goal.id)
                ms_text = ""
                if milestones:
                    ms_lines = []
                    for m in milestones:
                        icon = "done" if m.completed else "pending"
                        ms_lines.append(f"    [{icon}] {m.title} ({m.progress}%)")
                    ms_text = "\n  Milestones:\n" + "\n".join(ms_lines)

                deadline = goal.target_date.strftime("%Y-%m-%d") if goal.target_date else "No deadline"
                return Response(
                    success=True,
                    message=f"Goal: {goal.title}\n"
                            f"  Progress: {goal.progress}%\n"
                            f"  Priority: {goal.priority}\n"
                            f"  Deadline: {deadline}\n"
                            f"  Status: {goal.status}"
                            f"{ms_text}",
                )

    # Show all goals summary
    summary = service.get_progress_summary()
    goals = service.get_goals(parent_only=True, status="active")

    if not goals:
        return Response(
            success=True,
            message=f"Goals: {summary['total']} total, {summary['completed']} completed. No active goals.",
        )

    lines = [f"Active Goals ({len(goals)}):\n"]
    for goal in goals[:10]:
        bar_filled = int(goal.progress / 10)
        bar = "=" * bar_filled + "-" * (10 - bar_filled)
        deadline = goal.target_date.strftime("%Y-%m-%d") if goal.target_date else ""
        lines.append(f"  [{bar}] {goal.progress}% {goal.title} {deadline}")

    goal_data = [
        {"id": g.id, "title": g.title, "progress": g.progress}
        for g in goals
    ]

    return Response(
        success=True,
        message="\n".join(lines),
        data=goal_data,
    )


def handle_set_energy(intent: Intent, context: Context) -> Response:
    """Handle set energy level intent."""
    content = intent.entities.get("content", "")

    # Parse energy level from content or entities
    energy = None

    if "energy_level" in intent.entities:
        energy = intent.entities["energy_level"]
    else:
        # Try to extract number
        import re
        number_match = re.search(r'\d+', content)
        if number_match:
            energy = int(number_match.group())
        else:
            # Word-based
            energy_words = {"high": 8, "medium": 5, "low": 3}
            for word, level in energy_words.items():
                if word in content.lower():
                    energy = level
                    break

    if energy is None:
        return Response(success=False, message="What's your energy level? (1-10 or high/medium/low)")

    energy = max(1, min(10, energy))

    # Store in memory if available
    from jarvis.core.memory import MemoryEngine
    # We'd need the memory engine here — for now just acknowledge
    return Response(
        success=True,
        message=f"Energy level set to {energy}/10. "
                f"{'Great energy! Time for deep work.' if energy >= 7 else 'Consider lighter tasks.' if energy <= 4 else 'Solid. Ready for regular tasks.'}",
        data={"energy": energy},
    )


def handle_delete_task(intent: Intent, context: Context) -> Response:
    """Handle delete task intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    from jarvis.skills.tasks import TaskService
    from jarvis.db.models import TaskStatus

    content = intent.entities.get("content", "")
    service = TaskService(context.db)

    tasks = service.list(status=TaskStatus.PENDING, limit=50)

    for task in tasks:
        if content.lower() in task.title.lower():
            service.delete(task.id)
            return Response(
                success=True,
                message=f"Deleted: {task.title}",
            )

    return Response(
        success=False,
        message=f"Task '{content}' not found. Try listing your tasks first.",
    )
