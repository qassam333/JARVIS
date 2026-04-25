# API Layer Documentation

> **Purpose**: REST API to support the Web Dashboard UI (React/Vite).

---

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER                              │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Web UI    │    │  QuickShell  │    │   Scripts    │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │          │
│         └──────────────────┼──────────────────┘          │
│                            │                               │
│                            ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             FastAPI Backend (Port 8080)               │  │
│  │                                                         │  │
│  │  GET    /api/dashboard                                 │  │
│  │  GET    /api/tasks                                     │  │
│  │  POST   /api/tasks                                     │  │
│  │  POST   /api/tasks/{id}/complete                       │  │
│  │  GET    /api/habits                                    │  │
│  │  POST   /api/habits/{id}/log                           │  │
│  │  ...                                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                               │
│                            ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   JARVIS Core                         │  │
│  │          (Services, Skills, SQLite DB)                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
jarvis/
└── dashboard/
    ├── frontend/           # React + Vite UI
    └── backend/
        ├── __init__.py
        ├── main.py         # FastAPI application and routes
        └── static/         # Static premium dashboard fallback
```

---

## Implemented API Endpoints

The API is fully functional and powers the new Web Dashboard and QuickShell widgets. 

### Profile & Dashboard
- `GET /api/profile` - Get user profile and graduation countdown.
- `GET /api/dashboard` - Get all combined dashboard data for QuickShell widgets.
- `GET /api/quotes` - Get a motivational quote.
- `GET /api/system` - Get system health and overall stats.

### Tasks
- `GET /api/tasks?status=pending&limit=20` - List tasks with optional filters.
- `POST /api/tasks` - Create a new task (expects `title`, `priority`, `energy`).
- `POST /api/tasks/{task_id}/complete` - Mark a task as completed.
- `DELETE /api/tasks/{task_id}` - Delete a task.

### Habits
- `GET /api/habits` - Get all habits and their status for today.
- `POST /api/habits/{habit_id}/log` - Log a habit completion for today.
- `DELETE /api/habits/{habit_id}/log` - Remove a habit log for today.

### Goals
- `GET /api/goals` - Get all goals, their milestones, and overall progress.
- `PUT /api/goals/{goal_id}/progress` - Update progress value for a specific goal.

### Briefing & Reviews
- `GET /api/reviews/weekly` - Get weekly stats and completion chart data.
- `GET /api/briefing` - Generate and retrieve the daily briefing text.

---

## API Usage Example

### List Tasks

```bash
curl http://localhost:8080/api/tasks?status=pending
```

Response:
```json
{
  "tasks": [
    {
      "id": "abc-123",
      "title": "Study math",
      "energy_level": 7,
      "priority": 5,
      "status": "pending",
      "deadline": "2024-01-20T14:00:00Z",
      "created_at": "2024-01-15T10:00:00Z",
      "completed_at": null
    }
  ]
}
```

### System Health Check

```bash
curl http://localhost:8080/api/system
```

Response:
```json
{
  "status": "online",
  "version": "0.2.0",
  "stats": {
    "pending_tasks": 10,
    "completed_tasks": 45,
    "active_habits": 5,
    "active_goals": 2
  }
}
```

---

## Running the Dashboard and API

The backend serves both the API endpoints under `/api` and the React frontend on the root path `/`. 

```bash
# Start the full dashboard stack (API + Frontend)
cd jarvis/dashboard
./start.sh

# Or start just the FastAPI backend manually
python -m jarvis.dashboard.backend.main

# API docs are automatically generated and available at:
# http://localhost:8080/docs  (Swagger UI)
# http://localhost:8080/redoc (ReDoc)
```

---

<div align="center">

**API: Connect anything to JARVIS.**

</div>
