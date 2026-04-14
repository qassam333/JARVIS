"""University data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class AssignmentType(str, Enum):
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    EXAM = "exam"
    LECTURE = "lecture"
    PROJECT = "project"
    READING = "reading"


class AssignmentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    IMPORTED = "imported"


@dataclass
class Course:
    """University course."""

    id: str
    name: str
    code: Optional[str] = None
    semester: Optional[str] = None
    instructor: Optional[str] = None
    url: Optional[str] = None
    credentials_id: Optional[str] = None


@dataclass
class Assignment:
    """University assignment from LMS."""

    id: str
    course_id: str
    title: str
    type: AssignmentType = AssignmentType.ASSIGNMENT
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    url: Optional[str] = None
    status: AssignmentStatus = AssignmentStatus.PENDING
    task_id: Optional[str] = None
    raw_data: dict = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def course_name(self) -> str:
        return getattr(self, "_course_name", "Unknown Course")


@dataclass
class Credentials:
    """University login credentials (stored encrypted)."""

    id: str
    service: str  # "moodle", "canvas", etc.
    base_url: str
    username: Optional[str] = None
    last_sync: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Encrypted fields (never stored plaintext)
    _encrypted_password: Optional[bytes] = None
    _encrypted_token: Optional[bytes] = None


@dataclass
class SyncResult:
    """Result of a sync operation."""

    success: bool
    items_fetched: int = 0
    tasks_created: int = 0
    courses_updated: int = 0
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    synced_at: datetime = field(default_factory=datetime.utcnow)
