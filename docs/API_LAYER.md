# API Layer Documentation

> **Purpose**: REST API structure for future web UI and external integrations.

---

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER                              │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Web UI    │    │  Mobile App  │    │   Scripts    │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │          │
│         └──────────────────┼──────────────────┘          │
│                            │                               │
│                            ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    REST API                           │  │
│  │                                                         │  │
│  │  GET    /api/v1/tasks                                  │  │
│  │  POST   /api/v1/tasks                                  │  │
│  │  GET    /api/v1/tasks/{id}                            │  │
│  │  PUT    /api/v1/tasks/{id}                            │  │
│  │  DELETE /api/v1/tasks/{id}                            │  │
│  │                                                         │  │
│  │  GET    /api/v1/notes                                  │  │
│  │  POST   /api/v1/notes                                  │  │
│  │  ...                                                   │  │
│  │                                                         │  │
│  │  GET    /api/v1/health                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                               │
│                            ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Authentication (Future)                    │  │
│  │  • API Keys                                           │  │
│  │  • JWT tokens                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                               │
│                            ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   JARVIS Core                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
jarvis/
└── api/
    ├── __init__.py
    ├── app.py              # FastAPI app setup
    ├── router.py           # Route definitions
    ├── routes/
    │   ├── __init__.py
    │   ├── tasks.py        # Task endpoints
    │   ├── notes.py        # Note endpoints
    │   ├── knowledge.py    # Knowledge endpoints
    │   └── health.py       # Health check
    ├── schemas/            # Pydantic models
    │   ├── __init__.py
    │   ├── task.py
    │   ├── note.py
    │   └── common.py
    └── middleware/
        ├── __init__.py
        ├── auth.py         # Authentication
        └── logging.py      # Request logging
```

---

## API Schema

### Common Response

```python
# schemas/common.py

from pydantic import BaseModel
from typing import TypeVar, Generic, Optional
from datetime import datetime

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginatedResponse(ApiResponse[T]):
    """Paginated response"""
    data: Optional[list[T]] = None
    page: int = 1
    per_page: int = 20
    total: int = 0
    total_pages: int = 0

class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    error_code: str
    details: Optional[dict] = None
```

### Task Schema

```python
# schemas/task.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskSource(str, Enum):
    MANUAL = "manual"
    MOODLE = "moodle"

class TaskCreate(BaseModel):
    """Schema for creating a task"""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    energy_level: int = Field(5, ge=1, le=10)
    deadline: Optional[datetime] = None
    priority: int = Field(3, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    
    @field_validator("deadline")
    @classmethod
    def deadline_not_in_past(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError("Deadline cannot be in the past")
        return v
    
    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    deadline: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[TaskStatus] = None
    tags: Optional[list[str]] = None

class TaskResponse(BaseModel):
    """Task in API response"""
    id: str
    title: str
    description: Optional[str]
    energy_level: int
    deadline: Optional[datetime]
    priority: int
    status: TaskStatus
    source: TaskSource
    tags: list[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True
```

---

## Router Implementation

### Main App

```python
# api/app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jarvis.api.router import api_router
from jarvis.api.middleware.logging import LoggingMiddleware
from jarvis.utils.logger import setup_logger

logger = setup_logger("jarvis.api")

def create_app() -> FastAPI:
    app = FastAPI(
        title="JARVIS API",
        description="Local AI Assistant API",
        version="0.1.0",
        docs_url="/docs",  # Swagger UI
        redoc_url="/redoc"  # ReDoc
    )
    
    # CORS (configure for your needs)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Web UI
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Middleware
    app.add_middleware(LoggingMiddleware)
    
    # Routes
    app.include_router(api_router, prefix="/api/v1")
    
    return app

app = create_app()
```

### Task Routes

```python
# api/routes/tasks.py

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from jarvis.api.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskStatus
)
from jarvis.api.schemas.common import ApiResponse, PaginatedResponse
from jarvis.skills.tasks import TasksSkill

router = APIRouter(prefix="/tasks", tags=["Tasks"])
tasks_skill = TasksSkill()

@router.get("", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None),
    source: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """List all tasks with optional filters"""
    
    tasks = tasks_skill.list(
        status=status.value if status else None,
        source=source,
        page=page,
        per_page=per_page
    )
    
    return PaginatedResponse(
        success=True,
        data=tasks,
        page=page,
        per_page=per_page,
        total=tasks_skill.count(status=status.value if status else None),
        total_pages=(tasks_skill.count() + per_page - 1) // per_page
    )

@router.post("", response_model=ApiResponse[TaskResponse])
async def create_task(task: TaskCreate):
    """Create a new task"""
    
    created = tasks_skill.add(
        title=task.title,
        description=task.description,
        energy_level=task.energy_level,
        deadline=task.deadline,
        priority=task.priority,
        tags=task.tags
    )
    
    return ApiResponse(
        success=True,
        data=TaskResponse.model_validate(created),
        message="Task created successfully"
    )

@router.get("/{task_id}", response_model=ApiResponse[TaskResponse])
async def get_task(task_id: str):
    """Get a specific task"""
    
    task = tasks_skill.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return ApiResponse(
        success=True,
        data=TaskResponse.model_validate(task)
    )

@router.put("/{task_id}", response_model=ApiResponse[TaskResponse])
async def update_task(task_id: str, task: TaskUpdate):
    """Update a task"""
    
    updated = tasks_skill.update(task_id, **task.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return ApiResponse(
        success=True,
        data=TaskResponse.model_validate(updated),
        message="Task updated successfully"
    )

@router.delete("/{task_id}", response_model=ApiResponse)
async def delete_task(task_id: str):
    """Delete a task"""
    
    success = tasks_skill.delete(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return ApiResponse(
        success=True,
        message="Task deleted successfully"
    )

@router.post("/{task_id}/complete", response_model=ApiResponse[TaskResponse])
async def complete_task(task_id: str):
    """Mark task as completed"""
    
    task = tasks_skill.complete(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return ApiResponse(
        success=True,
        data=TaskResponse.model_validate(task),
        message="Task completed"
    )
```

---

## Health Check

```python
# api/routes/health.py

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from jarvis.db.database import Database

router = APIRouter(tags=["Health"])

class HealthStatus(BaseModel):
    status: str
    database: str
    voice: str
    timestamp: datetime

@router.get("/health", response_model=HealthStatus)
async def health_check():
    """Check system health"""
    
    # Check database
    try:
        db = Database()
        db.execute("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"
    
    # Check voice (if enabled)
    voice_status = "disabled"  # or "ok" if configured
    
    overall = "ok" if db_status == "ok" else "degraded"
    
    return HealthStatus(
        status=overall,
        database=db_status,
        voice=voice_status,
        timestamp=datetime.utcnow()
    )
```

---

## API Usage Examples

### List Tasks

```bash
curl http://localhost:8000/api/v1/tasks?status=pending&page=1
```

Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "abc-123",
      "title": "Study math",
      "energy_level": 7,
      "deadline": "2024-01-20T14:00:00Z",
      "priority": 5,
      "status": "pending",
      "source": "manual",
      "tags": ["study"],
      "created_at": "2024-01-15T10:00:00Z",
      "completed_at": null
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 1,
  "total_pages": 1,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Create Task

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New task",
    "energy_level": 5,
    "priority": 3
  }'
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "ok",
  "database": "ok",
  "voice": "disabled",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Running the API

```bash
# Start API server
jarvis api serve

# Or with uvicorn directly
uvicorn jarvis.api.app:app --host 0.0.0.0 --port 8000

# API docs available at
# http://localhost:8000/docs  (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

---

## Future: Authentication

```python
# api/middleware/auth.py (future)

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key not in get_valid_api_keys():
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Usage:
@router.get("/tasks", dependencies=[Depends(verify_api_key)])
async def list_tasks():
    ...
```

---

<div align="center">

**API: Connect anything to JARVIS.**

</div>
