"""JARVIS Dashboard Backend - FastAPI Server."""

import os
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from jarvis.db.database import Database
from jarvis.db.models import TaskStatus
from jarvis.skills.profile import ProfileService
from jarvis.skills.goals import GoalService
from jarvis.skills.habits import HabitService
from jarvis.skills.reviews import ReviewService
from jarvis.skills.tasks import TaskService
from jarvis.skills.briefing import BriefingService

app = FastAPI(
    title="JARVIS Dashboard",
    description="Your personal life management dashboard",
    version="1.0.0",
)

from jarvis.utils.config import config
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
if hasattr(config, "_config") and hasattr(config._config, "api") and hasattr(config._config.api, "cors_origins"):
    for o in config._config.api.cors_origins:
        if o not in origins:
            origins.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

DB_PATH = os.environ.get("JARVIS_DB_PATH", "./data/jarvis.db")
db = Database(Path(DB_PATH))

profile_service = ProfileService(db)
goal_service = GoalService(db)
habit_service = HabitService(db)
review_service = ReviewService(db)
task_service = TaskService(db)
briefing_service = BriefingService(db)


@app.get("/api/profile")
async def get_profile():
    """Get user profile with grad countdown."""
    profile = profile_service.get_profile()

    grad_deadline = profile.grad_deadline
    today = date.today()

    if grad_deadline:
        days_left = (grad_deadline - today).days
    else:
        days_left = None

    day_name = today.strftime("%A")
    is_grad_day = day_name.lower() in ["saturday", "sunday", "monday"]

    return {
        "name": profile.name or "User",
        "work_style": profile.work_style,
        "grad_deadline": grad_deadline.isoformat() if grad_deadline else None,
        "graduation_date": profile.graduation_date.isoformat()
        if profile.graduation_date
        else None,
        "days_until_grad": days_left,
        "today": today.isoformat(),
        "day_name": day_name,
        "is_grad_day": is_grad_day,
        "job_preference": profile.job_preference,
    }


@app.get("/api/habits")
async def get_habits():
    """Get all habits with today's status."""
    habits = habit_service.get_habits()
    today = date.today()
    today_logs = {log.habit_id: log for log in habit_service.get_today_logs()}

    result = []
    for habit in habits:
        today_log = today_logs.get(habit.id)
        stats = habit_service.get_stats(habit.id)

        result.append(
            {
                "id": habit.id,
                "name": habit.name,
                "frequency": habit.frequency,
                "time_of_day": habit.time_of_day,
                "current_streak": habit.current_streak,
                "best_streak": habit.best_streak,
                "completed_today": habit.id in today_logs,
                "pages": today_log.pages if today_log else None,
                "duration": today_log.duration_minutes if today_log else None,
                "linked_area_id": habit.linked_area_id,
                "last_30_days": stats.get("last_30_days_completion", 0),
            }
        )

    return {"habits": result}


@app.post("/api/habits/{habit_id}/log")
async def log_habit(
    habit_id: str, pages: Optional[int] = None, duration: Optional[int] = None
):
    """Log habit completion."""
    habit = habit_service.get_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    habit_service.log_habit(habit_id, pages=pages, duration_minutes=duration)
    return {"success": True, "habit_id": habit_id}


@app.delete("/api/habits/{habit_id}/log")
async def unlog_habit(habit_id: str):
    """Remove habit log for today."""
    habit_service.unlog_habit(habit_id)
    return {"success": True, "habit_id": habit_id}


@app.get("/api/goals")
async def get_goals():
    """Get all goals with progress."""
    goals = goal_service.get_goals(parent_only=True)

    result = []
    for goal in goals:
        milestones = goal_service.get_milestones(goal.id)
        area = profile_service.get_area(goal.area_id) if goal.area_id else None

        result.append(
            {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "area_id": goal.area_id,
                "area_name": area.name if area else None,
                "area_color": area.color if area else "#6B7280",
                "progress": goal.progress,
                "priority": goal.priority,
                "status": goal.status,
                "target_date": goal.target_date.isoformat()
                if goal.target_date
                else None,
                "milestones": [
                    {
                        "id": m.id,
                        "title": m.title,
                        "progress": m.progress,
                        "completed": m.completed,
                    }
                    for m in milestones
                ],
            }
        )

    return {"goals": result}


@app.put("/api/goals/{goal_id}/progress")
async def update_goal_progress(goal_id: str, progress: int):
    """Update goal progress."""
    goal = goal_service.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal_service.update_progress(goal_id, progress)
    return {"success": True, "goal_id": goal_id, "progress": progress}


@app.get("/api/reviews/weekly")
async def get_weekly_stats():
    """Get weekly statistics."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    habit_logs = db.query(
        """SELECT hl.*, h.name, h.frequency 
           FROM habit_logs hl
           JOIN habits h ON hl.habit_id = h.id
           WHERE hl.date >= ? AND hl.completed = 1""",
        (week_start.isoformat(),),
    )

    all_habits = db.query("SELECT id, name, frequency FROM habits WHERE is_active = 1")

    days_in_week = (today - week_start).days + 1
    expected_logs = len(all_habits) * days_in_week

    daily_counts = {}
    for i in range(7):
        day = week_start + timedelta(days=i)
        daily_counts[day.strftime("%a")] = 0

    for log in habit_logs:
        day_name = datetime.fromisoformat(log["date"]).strftime("%a")
        if day_name in daily_counts:
            daily_counts[day_name] += 1

    max_habits = max(len(all_habits), 1)

    chart_data = []
    day_names_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for day_name in day_names_en:
        count = daily_counts.get(day_name, 0)
        chart_data.append(
            {
                "day": day_name,
                "completed": count,
                "total": len(all_habits),
                "percentage": int((count / max_habits) * 100) if max_habits > 0 else 0,
            }
        )

    completion_rate = (
        int((len(habit_logs) / expected_logs * 100)) if expected_logs > 0 else 0
    )

    return {
        "week_start": week_start.isoformat(),
        "week_end": (week_start + timedelta(days=6)).isoformat(),
        "total_completed": len(habit_logs),
        "total_expected": expected_logs,
        "completion_rate": completion_rate,
        "habits_tracked": len(all_habits),
        "chart_data": chart_data,
    }


@app.get("/api/quotes")
async def get_quote():
    """Get motivational quote."""
    quotes = [
        "Every line of code brings O4 Studio closer to reality.",
        "The grind today builds the studio tomorrow.",
        "No one else is going to build your games for you.",
        "Your future self will thank you for the work you do now.",
        "LINKIT won't finish itself. Get to it.",
        "O4 Studio starts with today's work.",
        "Discipline beats motivation. Keep showing up.",
        "The only way out is through. Keep pushing.",
        "49 days to graduation. Make them count.",
        "Every habit completed is progress toward O4 Studio.",
        "Stay focused. Stay disciplined. Ship the game.",
        "The dream is free. The grind is where you earn it.",
    ]

    import random

    return {"quote": random.choice(quotes)}


@app.get("/api/dashboard")
async def get_dashboard():
    """Get all dashboard data combined for QuickShell widget."""
    profile_data = await get_profile()
    habits_data = await get_habits()
    weekly_data = await get_weekly_stats()
    quote_data = await get_quote()

    habits_completed = sum(1 for h in habits_data["habits"] if h["completed_today"])

    return {
        "days_until_grad": profile_data["days_until_grad"],
        "day_name": profile_data["day_name"],
        "is_grad_day": profile_data["is_grad_day"],
        "habits": habits_data["habits"],
        "habits_completed": habits_completed,
        "habits_total": len(habits_data["habits"]),
        "quote": quote_data["quote"],
        "completion_rate": weekly_data["completion_rate"],
        "weekly_completion": weekly_data["completion_rate"],
    }


# ---- Task endpoints ----

@app.get("/api/tasks")
async def get_tasks(status: str = "pending", limit: int = 20):
    """Get tasks with optional status filter."""
    status_enum = TaskStatus(status) if status else None
    tasks = task_service.list(status=status_enum, limit=limit)

    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "energy_level": t.energy_level,
                "priority": t.priority,
                "status": t.status,
                "deadline": t.deadline.isoformat() if t.deadline else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in tasks
        ]
    }


@app.post("/api/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    """Mark a task as completed."""
    task = task_service.complete(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "task_id": task_id, "title": task.title}


@app.post("/api/tasks")
async def create_task(title: str, priority: int = 3, energy: int = 5):
    """Create a new task."""
    from jarvis.db.models import TaskCreate
    task = task_service.create(TaskCreate(title=title, priority=priority, energy_level=energy))
    return {"success": True, "task_id": task.id, "title": task.title}


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task."""
    if task_service.delete(task_id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Task not found")


# ---- Briefing endpoint ----

@app.get("/api/briefing")
async def get_briefing():
    """Get daily briefing."""
    profile_data = await get_profile()
    user_name = profile_data.get("name")
    briefing_text = briefing_service.generate(user_name=user_name)
    
    pending_count = task_service.count(TaskStatus.PENDING)
    due_today = len(task_service.get_due_today())
    
    return {
        "briefing": briefing_text,
        "quick": briefing_service.quick_briefing(),
        "pending_tasks": pending_count,
        "due_today": due_today,
    }


# ---- System status ----

@app.get("/api/system")
async def get_system_status():
    """Get system health and stats."""
    pending = task_service.count(TaskStatus.PENDING)
    completed = task_service.count(TaskStatus.COMPLETED)
    habits = habit_service.get_habits()
    goals = goal_service.get_goals(parent_only=True)
    
    return {
        "status": "online",
        "version": "0.2.0",
        "stats": {
            "pending_tasks": pending,
            "completed_tasks": completed,
            "active_habits": len(habits),
            "active_goals": len([g for g in goals if g.status == "active"]),
        }
    }


@app.get("/")
async def root():
    """Serve the JARVIS Dashboard."""
    # Serve Vite-built React frontend
    html_path = Path(__file__).parent.parent / "frontend" / "dist" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
        
    # Fallback to premium static dashboard
    premium_path = Path(__file__).parent / "static" / "index.html"
    if premium_path.exists():
        return HTMLResponse(content=premium_path.read_text())

    return HTMLResponse(
        content="""
        <html>
            <head><title>JARVIS Dashboard</title></head>
            <body>
                <h1>JARVIS Dashboard</h1>
                <p>Frontend not built.</p>
            </body>
        </html>
        """
    )


# Serve static files for the premium dashboard
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# Serve assets for the React frontend
_react_assets_dir = Path(__file__).parent.parent / "frontend" / "dist" / "assets"
if _react_assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(_react_assets_dir)), name="assets")


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the dashboard server."""
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
