"""Moodle LMS scraper implementation."""

import time
import uuid
from datetime import datetime
from typing import Optional
import re

import httpx

from jarvis.skills.university.base import (
    UniversityScraper,
    AuthenticationError,
    NetworkError,
    ParseError,
)
from jarvis.skills.university.models import (
    Course,
    Assignment,
    AssignmentType,
    AssignmentStatus,
)
from jarvis.utils.logger import get_logger

logger = get_logger("skills.university.moodle")


class MoodleScraper(UniversityScraper):
    """Scraper for Moodle LMS."""

    RATE_LIMIT_DELAY = 2.0  # Seconds between requests

    def __init__(self):
        self._last_request = 0
        self._client: Optional[httpx.Client] = None

    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self._last_request
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request = time.time()

    def authenticate(self, credentials: tuple) -> dict:
        """
        Authenticate with Moodle.

        Args:
            credentials: Tuple of (username, password, base_url)

        Returns:
            Dict with token and user info
        """
        username, password, base_url = credentials

        try:
            self._client = httpx.Client(timeout=30.0)

            # Try Web Services token first
            response = self._client.get(
                f"{base_url}/login/token.php",
                params={
                    "service": "moodle_mobile_app",
                    "username": username,
                    "password": password,
                },
            )

            data = response.json()

            if "token" in data:
                logger.info("Authenticated via Web Services API")
                return {
                    "token": data["token"],
                    "base_url": base_url,
                    "userid": data.get("userid"),
                }

            # Fallback to cookies
            login_response = self._client.post(
                f"{base_url}/login/index.php",
                data={
                    "username": username,
                    "password": password,
                },
            )

            if "loginto" in login_response.text or login_response.status_code == 303:
                logger.info("Authenticated via web login")
                return {
                    "base_url": base_url,
                    "cookies": dict(login_response.cookies),
                }

            raise AuthenticationError("Invalid credentials")

        except httpx.RequestError as e:
            raise NetworkError(f"Connection failed: {e}")
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {e}")

    def get_courses(self, session: dict) -> list[Course]:
        """Fetch enrolled courses."""
        base_url = session["base_url"]

        if "token" in session:
            params = {
                "wstoken": session["token"],
                "moodlewsrestformat": "json",
                "wsfunction": "core_enrol_get_users_courses",
                "userid": "self",
            }
        else:
            raise AuthenticationError("No valid session")

        try:
            self._rate_limit()
            response = self._client.get(
                f"{base_url}/webservice/rest/server.php", params=params
            )

            courses = []
            for item in response.json():
                course = Course(
                    id=str(item["id"]),
                    name=item["fullname"],
                    code=item.get("shortname"),
                    url=f"{base_url}/course/view.php?id={item['id']}",
                )
                courses.append(course)

            logger.info(f"Fetched {len(courses)} courses")
            return courses

        except Exception as e:
            logger.error(f"Failed to fetch courses: {e}")
            return []

    def get_assignments(self, session: dict, course: Course) -> list[Assignment]:
        """Fetch assignments for a course."""
        base_url = session["base_url"]

        if "token" not in session:
            return []

        try:
            self._rate_limit()
            response = self._client.get(
                f"{base_url}/webservice/rest/server.php",
                params={
                    "wstoken": session["token"],
                    "moodlewsrestformat": "json",
                    "wsfunction": "mod_assign_get_assignments",
                    "courseids[0]": course.id,
                },
            )

            assignments = []
            data = response.json()

            for course_data in data.get("courses", []):
                for assign in course_data.get("assignments", []):
                    due_timestamp = assign.get("duedate", 0)
                    due_date = (
                        datetime.fromtimestamp(due_timestamp) if due_timestamp else None
                    )

                    assignment = Assignment(
                        id=str(uuid.uuid4()),
                        course_id=course.id,
                        title=assign["name"],
                        type=AssignmentType.ASSIGNMENT,
                        description=self._clean_html(assign.get("intro", "")),
                        due_date=due_date,
                        url=f"{base_url}/mod/assign/view.php?id={assign.get('cmid')}",
                        status=AssignmentStatus.PENDING,
                        raw_data=assign,
                    )
                    assignments.append(assignment)

            logger.info(f"Fetched {len(assignments)} assignments for {course.name}")
            return assignments

        except Exception as e:
            logger.error(f"Failed to fetch assignments: {e}")
            return []

    def get_quizzes(self, session: dict, course: Course) -> list[Assignment]:
        """Fetch quizzes for a course."""
        base_url = session["base_url"]

        if "token" not in session:
            return []

        try:
            self._rate_limit()
            response = self._client.get(
                f"{base_url}/webservice/rest/server.php",
                params={
                    "wstoken": session["token"],
                    "moodlewsrestformat": "json",
                    "wsfunction": "mod_quiz_get_quizzes_by_courses",
                    "courseids[0]": course.id,
                },
            )

            quizzes = []
            for quiz in response.json().get("quizzes", []):
                time_open = quiz.get("timeopen", 0)
                time_close = quiz.get("timeclose", 0)

                quiz_assignment = Assignment(
                    id=str(uuid.uuid4()),
                    course_id=course.id,
                    title=quiz["name"],
                    type=AssignmentType.QUIZ,
                    description=f"Time limit: {quiz.get('timelimit', 0) // 60} minutes",
                    due_date=datetime.fromtimestamp(time_close) if time_close else None,
                    url=f"{base_url}/mod/quiz/view.php?id={quiz.get('cmid')}",
                    status=AssignmentStatus.PENDING,
                    raw_data=quiz,
                )
                quizzes.append(quiz_assignment)

            logger.info(f"Fetched {len(quizzes)} quizzes for {course.name}")
            return quizzes

        except Exception as e:
            logger.error(f"Failed to fetch quizzes: {e}")
            return []

    def get_events(self, session: dict) -> list[Assignment]:
        """Fetch calendar events (lectures)."""
        base_url = session["base_url"]

        if "token" not in session:
            return []

        try:
            self._rate_limit()

            # Get events for next 30 days
            now = datetime.now()
            end_time = int((now.timestamp() + 30 * 24 * 3600))

            response = self._client.get(
                f"{base_url}/webservice/rest/server.php",
                params={
                    "wstoken": session["token"],
                    "moodlewsrestformat": "json",
                    "wsfunction": "core_calendar_get_calendar_events",
                    "timesortfrom": int(now.timestamp()),
                    "timesortto": end_time,
                },
            )

            events = []
            for event in response.json().get("events", []):
                if event.get("eventtype") == "course":
                    assignment = Assignment(
                        id=str(uuid.uuid4()),
                        course_id=str(event.get("courseid", "")),
                        title=event["name"],
                        type=AssignmentType.LECTURE,
                        description=self._clean_html(event.get("description", "")),
                        due_date=datetime.fromtimestamp(event["timestart"]),
                        url=event.get("url"),
                        status=AssignmentStatus.PENDING,
                        raw_data=event,
                    )
                    events.append(assignment)

            logger.info(f"Fetched {len(events)} events")
            return events

        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            return []

    def logout(self, session: dict):
        """Logout and close connection."""
        if self._client:
            try:
                if "token" in session:
                    base_url = session["base_url"]
                    self._client.get(
                        f"{base_url}/login/logout.php",
                        params={"wstoken": session["token"]},
                    )
            except Exception as e:
                logger.debug(f"Logout error: {e}")
            finally:
                self._client.close()
                self._client = None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        clean = re.sub(r"<[^>]+>", "", text)
        clean = clean.replace("&nbsp;", " ").replace("&amp;", "&")
        return clean.strip()
