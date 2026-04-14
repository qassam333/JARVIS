"""User profile management service."""

import json
from datetime import date, datetime
from typing import Optional, Any
from dataclasses import dataclass, field

from jarvis.utils.logger import get_logger

logger = get_logger("skills.profile")


@dataclass
class UserProfile:
    id: int
    name: Optional[str]
    explicit_preferences: dict[str, Any]
    learned_patterns: dict[str, Any]
    work_style: str
    grad_deadline: Optional[date]
    graduation_date: Optional[date]
    job_preference: str
    preferred_language: str
    accountability_style: str


@dataclass
class LifeArea:
    id: str
    name: str
    slug: str
    importance_weight: int
    color: str
    icon: Optional[str]
    description: Optional[str]
    created_at: Optional[datetime] = None


DEFAULT_LIFE_AREAS = [
    {
        "id": "career",
        "name": "Career",
        "slug": "career",
        "importance_weight": 9,
        "color": "#3B82F6",
        "icon": "briefcase",
        "description": "Job, UE5, grad project, portfolio",
    },
    {
        "id": "projects",
        "name": "Projects",
        "slug": "projects",
        "importance_weight": 8,
        "color": "#8B5CF6",
        "icon": "gamepad",
        "description": "LINKIT, Legendary Mansaf, Afterfall",
    },
    {
        "id": "learning",
        "name": "Learning",
        "slug": "learning",
        "importance_weight": 7,
        "color": "#10B981",
        "icon": "book",
        "description": "Python, English, French/German, IT",
    },
    {
        "id": "religion",
        "name": "Religion",
        "slug": "religion",
        "importance_weight": 9,
        "color": "#F59E0B",
        "icon": "moon",
        "description": "Quran, Prayer, Islamic knowledge",
    },
    {
        "id": "health",
        "name": "Health",
        "slug": "health",
        "importance_weight": 6,
        "color": "#EF4444",
        "icon": "heart",
        "description": "Exercise, sleep, diet",
    },
    {
        "id": "finance",
        "name": "Finance",
        "slug": "finance",
        "importance_weight": 5,
        "color": "#22C55E",
        "icon": "coins",
        "description": "Budget, savings, investments",
    },
    {
        "id": "personal",
        "name": "Personal",
        "slug": "personal",
        "importance_weight": 4,
        "color": "#EC4899",
        "icon": "user",
        "description": "Relationships, hobbies, travel",
    },
]


class ProfileService:
    def __init__(self, db):
        self.db = db
        self._ensure_initialized()

    def _ensure_initialized(self):
        row = self.db.query_one("SELECT id FROM user_profile WHERE id = 1")
        if not row:
            self.db.execute(
                """INSERT INTO user_profile (id, explicit_preferences, learned_patterns) 
                   VALUES (1, '{}', '{}')"""
            )
            logger.info("Created default user profile")

        areas = self.db.query("SELECT id FROM life_areas")
        if not areas:
            self._init_life_areas()
            logger.info("Initialized life areas")

    def _init_life_areas(self):
        for area in DEFAULT_LIFE_AREAS:
            self.db.execute(
                """INSERT INTO life_areas (id, name, slug, importance_weight, color, icon, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    area["id"],
                    area["name"],
                    area["slug"],
                    area["importance_weight"],
                    area["color"],
                    area["icon"],
                    area["description"],
                ),
            )

    def get_profile(self) -> UserProfile:
        row = self.db.query_one("SELECT * FROM user_profile WHERE id = 1")
        if not row:
            return UserProfile(
                id=1,
                name=None,
                explicit_preferences={},
                learned_patterns={},
                work_style="evening",
                grad_deadline=None,
                graduation_date=None,
                job_preference="hybrid",
                preferred_language="english",
                accountability_style="strict_motivational",
            )

        return UserProfile(
            id=row["id"],
            name=row["name"],
            explicit_preferences=json.loads(row["explicit_preferences"] or "{}"),
            learned_patterns=json.loads(row["learned_patterns"] or "{}"),
            work_style=row["work_style"] or "evening",
            grad_deadline=datetime.fromisoformat(row["grad_deadline"]).date()
            if row["grad_deadline"]
            else None,
            graduation_date=datetime.fromisoformat(row["graduation_date"]).date()
            if row["graduation_date"]
            else None,
            job_preference=row["job_preference"] or "hybrid",
            preferred_language=row["preferred_language"] or "english",
            accountability_style=row["accountability_style"] or "strict_motivational",
        )

    def update_profile(self, **kwargs):
        profile = self.get_profile()
        updates = []
        params = []

        for key, value in kwargs.items():
            if key in ["explicit_preferences", "learned_patterns"]:
                if isinstance(value, dict):
                    value = json.dumps(value)
            elif key in ["grad_deadline", "graduation_date"]:
                if value:
                    value = value.isoformat()

            col_map = {
                "name": "name",
                "work_style": "work_style",
                "job_preference": "job_preference",
                "preferred_language": "preferred_language",
                "accountability_style": "accountability_style",
                "grad_deadline": "grad_deadline",
                "graduation_date": "graduation_date",
                "explicit_preferences": "explicit_preferences",
                "learned_patterns": "learned_patterns",
            }

            if key in col_map:
                updates.append(f"{col_map[key]} = ?")
                params.append(value)

        if updates:
            params.append(1)
            self.db.execute(
                f"UPDATE user_profile SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                tuple(params),
            )
            logger.info(f"Updated profile: {list(kwargs.keys())}")

    def set_preference(self, key: str, value: Any):
        profile = self.get_profile()
        prefs = profile.explicit_preferences.copy()
        prefs[key] = value
        self.update_profile(explicit_preferences=prefs)

    def get_preference(self, key: str, default: Any = None) -> Any:
        profile = self.get_profile()
        return profile.explicit_preferences.get(key, default)

    def learn_pattern(self, pattern_key: str, value: Any, confidence: float = 0.5):
        profile = self.get_profile()
        patterns = profile.learned_patterns.copy()
        patterns[pattern_key] = {
            "value": value,
            "confidence": confidence,
            "updated": datetime.now().isoformat(),
        }
        self.update_profile(learned_patterns=patterns)

    def get_life_areas(self) -> list[LifeArea]:
        rows = self.db.query("SELECT * FROM life_areas ORDER BY importance_weight DESC")
        return [LifeArea(**dict(row)) for row in rows]

    def get_area(self, area_id: str) -> Optional[LifeArea]:
        row = self.db.query_one("SELECT * FROM life_areas WHERE id = ?", (area_id,))
        return LifeArea(**dict(row)) if row else None

    def update_area_importance(self, area_id: str, weight: int):
        self.db.execute(
            "UPDATE life_areas SET importance_weight = ? WHERE id = ?",
            (weight, area_id),
        )

    def get_peak_hours(self) -> list[str]:
        profile = self.get_profile()
        return profile.explicit_preferences.get("peak_hours", ["18:00-22:00"])

    def get_work_days(self) -> list[str]:
        profile = self.get_profile()
        return profile.explicit_preferences.get("work_days", ["sat", "sun", "mon"])

    def set_work_schedule(self, grad_days: list[str], work_hours: tuple[str, str]):
        self.set_preference("work_days", grad_days)
        self.set_preference(
            "work_hours", {"start": work_hours[0], "end": work_hours[1]}
        )

    def get_grad_deadline(self) -> Optional[date]:
        profile = self.get_profile()
        return profile.grad_deadline

    def get_days_until_grad(self) -> int:
        deadline = self.get_grad_deadline()
        if not deadline:
            return -1
        return (deadline - date.today()).days
