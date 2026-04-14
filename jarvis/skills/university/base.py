"""Abstract base scraper for university LMS systems."""

from abc import ABC, abstractmethod
from typing import Optional

from jarvis.skills.university.models import Course, Assignment, Credentials


class UniversityScraper(ABC):
    """Abstract base for university LMS scrapers."""

    @abstractmethod
    def authenticate(self, credentials: Credentials) -> str:
        """
        Authenticate and return session token.

        Args:
            credentials: User credentials

        Returns:
            Session token or cookie string
        """
        pass

    @abstractmethod
    def get_courses(self, session: str) -> list[Course]:
        """
        Fetch enrolled courses.

        Args:
            session: Authenticated session token

        Returns:
            List of Course objects
        """
        pass

    @abstractmethod
    def get_assignments(self, session: str, course: Course) -> list[Assignment]:
        """
        Fetch assignments for a course.

        Args:
            session: Authenticated session token
            course: Course to fetch assignments for

        Returns:
            List of Assignment objects
        """
        pass

    @abstractmethod
    def get_quizzes(self, session: str, course: Course) -> list[Assignment]:
        """
        Fetch quizzes for a course.

        Args:
            session: Authenticated session token
            course: Course to fetch quizzes for

        Returns:
            List of Assignment objects
        """
        pass

    @abstractmethod
    def get_events(self, session: str) -> list[Assignment]:
        """
        Fetch calendar events (lectures, etc.).

        Args:
            session: Authenticated session token

        Returns:
            List of Assignment objects
        """
        pass

    @abstractmethod
    def logout(self, session: str):
        """
        Logout and invalidate session.

        Args:
            session: Session token to invalidate
        """
        pass


class ScraperError(Exception):
    """Base exception for scraper errors."""

    pass


class AuthenticationError(ScraperError):
    """Authentication failed."""

    pass


class NetworkError(ScraperError):
    """Network connectivity issue."""

    pass


class ParseError(ScraperError):
    """Failed to parse LMS response."""

    pass
