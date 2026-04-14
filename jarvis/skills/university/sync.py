"""University sync orchestrator."""

import time
import json
import uuid
from datetime import datetime
from typing import Optional

from jarvis.skills.university.models import (
    Course,
    Assignment,
    AssignmentType,
    AssignmentStatus,
    SyncResult,
)
from jarvis.skills.university.moodle import MoodleScraper
from jarvis.skills.university.encryption import CredentialManager, Encryptor
from jarvis.skills.university.base import AuthenticationError, ScraperError
from jarvis.skills.tasks import TaskService
from jarvis.db.models import TaskCreate, TaskStatus
from jarvis.utils.logger import get_logger

logger = get_logger("skills.university.sync")


class UniversitySync:
    """Orchestrates university data sync."""

    def __init__(self, db):
        self.db = db
        self.encryptor = Encryptor()
        self.credential_manager = CredentialManager(db, self.encryptor)
        self.scraper = MoodleScraper()
        self.task_service = TaskService(db)

    def is_configured(self) -> bool:
        """Check if university is configured."""
        return self.credential_manager.has_credentials("moodle")

    def setup(self, base_url: str, username: str, password: str):
        """Setup university connection."""
        if self.is_configured():
            self.credential_manager.delete_credentials("moodle")

        cred_id = self.credential_manager.save_credentials(
            service="moodle",
            base_url=base_url.rstrip("/"),
            username=username,
            password=password,
        )

        logger.info(f"University credentials saved")
        return cred_id

    def sync(self, import_tasks: bool = True) -> SyncResult:
        """Execute full sync."""
        start_time = time.time()
        result = SyncResult(success=False)

        if not self.is_configured():
            result.errors.append("University not configured")
            return result

        try:
            # Get credentials
            username, password, base_url = self.credential_manager.get_credentials(
                "moodle"
            )

            # Authenticate
            logger.info("Authenticating with Moodle...")
            session = self.scraper.authenticate((username, password, base_url))
            result.authenticated = True

            # Fetch courses
            logger.info("Fetching courses...")
            courses = self.scraper.get_courses(session)
            result.courses_updated = len(courses)

            # Store courses
            for course in courses:
                self._save_course(course)

            # Fetch all assignments
            all_assignments = []
            for course in courses:
                assignments = self.scraper.get_assignments(session, course)
                quizzes = self.scraper.get_quizzes(session, course)
                all_assignments.extend(assignments)
                all_assignments.extend(quizzes)

            # Fetch events
            events = self.scraper.get_events(session)
            all_assignments.extend(events)

            result.items_fetched = len(all_assignments)

            # Logout
            self.scraper.logout(session)

            # Store assignments
            for assignment in all_assignments:
                self._save_assignment(assignment)

            # Import to tasks
            if import_tasks:
                tasks_created = self._import_to_tasks(all_assignments)
                result.tasks_created = tasks_created

            # Update sync timestamp
            self.credential_manager.update_last_sync("moodle")

            # Log sync
            self._log_sync(result)

            result.success = True
            logger.info(
                f"Sync completed: {result.items_fetched} items, {result.tasks_created} tasks"
            )

        except AuthenticationError as e:
            result.errors.append(f"Authentication failed: {e}")
            logger.error(f"Authentication error: {e}")

        except ScraperError as e:
            result.errors.append(f"Scraper error: {e}")
            logger.error(f"Scraper error: {e}")

        except Exception as e:
            result.errors.append(f"Unexpected error: {e}")
            logger.error(f"Sync error: {e}")

        finally:
            result.duration_seconds = time.time() - start_time

        return result

    def _save_course(self, course: Course):
        """Save or update course."""
        existing = self.db.query_one(
            "SELECT id FROM courses WHERE id = ?", (course.id,)
        )

        if existing:
            self.db.execute(
                """
                UPDATE courses SET name = ?, code = ?, instructor = ?
                WHERE id = ?
                """,
                (course.name, course.code, course.instructor, course.id),
            )
        else:
            self.db.execute(
                """
                INSERT INTO courses (id, name, code, semester, instructor, url)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    course.id,
                    course.name,
                    course.code,
                    course.semester,
                    course.instructor,
                    course.url,
                ),
            )

    def _save_assignment(self, assignment: Assignment):
        """Save or update assignment."""
        existing = self.db.query_one(
            "SELECT id, task_id FROM university_assignments WHERE id = ?",
            (assignment.id,),
        )

        raw_data_json = json.dumps(assignment.raw_data) if assignment.raw_data else "{}"
        due_date = assignment.due_date.isoformat() if assignment.due_date else None

        if existing:
            self.db.execute(
                """
                UPDATE university_assignments 
                SET title = ?, type = ?, description = ?, due_date = ?, 
                    status = ?, url = ?, raw_data = ?, fetched_at = ?
                WHERE id = ?
                """,
                (
                    assignment.title,
                    assignment.type.value,
                    assignment.description,
                    due_date,
                    assignment.status.value,
                    assignment.url,
                    raw_data_json,
                    datetime.utcnow().isoformat(),
                    assignment.id,
                ),
            )
        else:
            self.db.execute(
                """
                INSERT INTO university_assignments 
                (id, course_id, title, type, description, due_date, url, status, raw_data, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assignment.id,
                    assignment.course_id,
                    assignment.title,
                    assignment.type.value,
                    assignment.description,
                    due_date,
                    assignment.url,
                    assignment.status.value,
                    raw_data_json,
                    datetime.utcnow().isoformat(),
                ),
            )

    def _import_to_tasks(self, assignments: list[Assignment]) -> int:
        """Import assignments as tasks."""
        tasks_created = 0

        for assignment in assignments:
            # Skip if already imported
            if assignment.task_id:
                continue

            # Skip if no due date
            if not assignment.due_date:
                continue

            # Get course name
            course = self.db.query_one(
                "SELECT name FROM courses WHERE id = ?", (assignment.course_id,)
            )
            course_name = course["name"] if course else "University"

            # Map to task priority
            priority = {
                AssignmentType.EXAM: 5,
                AssignmentType.QUIZ: 4,
                AssignmentType.ASSIGNMENT: 3,
                AssignmentType.PROJECT: 3,
                AssignmentType.LECTURE: 2,
            }.get(assignment.type, 3)

            # Map to energy level
            energy = {
                AssignmentType.EXAM: 8,
                AssignmentType.QUIZ: 6,
                AssignmentType.ASSIGNMENT: 5,
                AssignmentType.PROJECT: 5,
                AssignmentType.LECTURE: 3,
            }.get(assignment.type, 5)

            # Create task
            task = self.task_service.create(
                TaskCreate(
                    title=f"[{course_name}] {assignment.title}",
                    description=assignment.description
                    or f"Type: {assignment.type.value}",
                    energy_level=energy,
                    deadline=assignment.due_date,
                    priority=priority,
                    source="moodle",
                )
            )

            # Link assignment to task
            self.db.execute(
                "UPDATE university_assignments SET task_id = ?, status = ? WHERE id = ?",
                (task.id, AssignmentStatus.IMPORTED.value, assignment.id),
            )

            tasks_created += 1

        return tasks_created

    def _log_sync(self, result: SyncResult):
        """Log sync result."""
        sync_id = str(uuid.uuid4())

        self.db.execute(
            """
            INSERT INTO sync_logs (id, sync_type, status, items_synced, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                sync_id,
                "university_moodle",
                "success" if result.success else "failed",
                result.items_fetched,
                "; ".join(result.errors) if result.errors else None,
                datetime.utcnow().isoformat(),
            ),
        )

    def get_assignments(
        self,
        status: Optional[AssignmentStatus] = None,
        assignment_type: Optional[AssignmentType] = None,
    ) -> list[dict]:
        """Get stored assignments."""
        conditions = ["1=1"]
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status.value)

        if assignment_type:
            conditions.append("type = ?")
            params.append(assignment_type.value)

        where = " AND ".join(conditions)

        rows = self.db.query(
            f"""
            SELECT ua.*, c.name as course_name
            FROM university_assignments ua
            LEFT JOIN courses c ON ua.course_id = c.id
            WHERE {where}
            ORDER BY ua.due_date ASC
            """,
            tuple(params),
        )

        return [dict(row) for row in rows]

    def get_courses(self) -> list[dict]:
        """Get stored courses."""
        rows = self.db.query("SELECT * FROM courses ORDER BY name")
        return [dict(row) for row in rows]

    def get_last_sync(self) -> Optional[datetime]:
        """Get last sync timestamp."""
        row = self.db.query_one(
            "SELECT last_sync FROM credentials WHERE service = ?", ("moodle",)
        )
        if row and row["last_sync"]:
            return datetime.fromisoformat(row["last_sync"])
        return None
