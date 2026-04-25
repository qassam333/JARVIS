"""Pydantic models for JARVIS data structures."""

from datetime import datetime, date, timezone
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskSource(str, Enum):
    MANUAL = "manual"
    MOODLE = "moodle"
    SCHEDULE = "schedule"


class TaskCreate(BaseModel):
    """Schema for creating a task."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    energy_level: int = Field(5, ge=1, le=10)
    deadline: Optional[datetime] = None
    priority: int = Field(3, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    source: TaskSource = TaskSource.MANUAL

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty")
        return stripped


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    deadline: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[TaskStatus] = None
    tags: Optional[list[str]] = None


class Task(BaseModel):
    """Full task model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    energy_level: int = 5
    deadline: Optional[datetime] = None
    priority: int = 3
    status: TaskStatus = TaskStatus.PENDING
    source: TaskSource = TaskSource.MANUAL
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    model_config = {"use_enum_values": True}


class NoteCreate(BaseModel):
    """Schema for creating a note."""

    title: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    """Schema for updating a note."""

    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    tags: Optional[list[str]] = None


class Note(BaseModel):
    """Full note model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    content: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeCreate(BaseModel):
    """Schema for creating knowledge."""

    fact: str = Field(..., min_length=1)
    category: Optional[str] = None
    source: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class KnowledgeUpdate(BaseModel):
    """Schema for updating knowledge."""

    fact: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[list[str]] = None


class Knowledge(BaseModel):
    """Full knowledge model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fact: str
    category: Optional[str] = None
    source: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DailyLogCreate(BaseModel):
    """Schema for creating daily log."""

    date: date
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    productivity_score: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None


class DailyLog(BaseModel):
    """Daily context log."""

    date: date
    energy_level: Optional[int] = None
    productivity_score: Optional[int] = None
    notes: Optional[str] = None
