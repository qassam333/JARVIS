"""Migration 002: Life Management System.

Creates tables for goals, habits, reviews, and enhanced user profile.
"""

from jarvis.db.migrations import Migration


class LifeManagementMigration(Migration):
    """Migration 002: Life management schema."""

    version = "002"
    description = "Life management - goals, habits, reviews, enhanced profile"

    def up(self, db) -> None:
        """Create life management tables."""

        db.execute("""
            CREATE TABLE IF NOT EXISTS life_areas (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                importance_weight INTEGER DEFAULT 5,
                color TEXT DEFAULT '#6B7280',
                icon TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY,
                name TEXT,
                explicit_preferences TEXT DEFAULT '{}',
                learned_patterns TEXT DEFAULT '{}',
                work_style TEXT DEFAULT 'evening',
                grad_deadline DATE,
                graduation_date DATE,
                job_preference TEXT DEFAULT 'hybrid',
                preferred_language TEXT DEFAULT 'english',
                accountability_style TEXT DEFAULT 'strict_motivational',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                area_id TEXT,
                parent_goal_id TEXT,
                target_date DATE,
                start_date DATE,
                progress INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'active',
                is_milestone INTEGER DEFAULT 0,
                linked_task_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (area_id) REFERENCES life_areas(id),
                FOREIGN KEY (parent_goal_id) REFERENCES goals(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                id TEXT PRIMARY KEY,
                goal_id TEXT NOT NULL,
                title TEXT NOT NULL,
                target_date DATE,
                progress INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                frequency TEXT DEFAULT 'daily',
                time_of_day TEXT DEFAULT 'evening',
                duration_minutes INTEGER,
                linked_goal_id TEXT,
                linked_area_id TEXT,
                current_streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                last_completed DATE,
                reminder_time TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (linked_goal_id) REFERENCES goals(id),
                FOREIGN KEY (linked_area_id) REFERENCES life_areas(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id TEXT PRIMARY KEY,
                habit_id TEXT NOT NULL,
                date DATE NOT NULL,
                completed INTEGER DEFAULT 1,
                pages INTEGER,
                duration_minutes INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits(id),
                UNIQUE(habit_id, date)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS daily_reviews (
                id TEXT PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                mood INTEGER,
                energy_level INTEGER,
                productivity_score INTEGER,
                completed_tasks INTEGER DEFAULT 0,
                planned_tasks INTEGER DEFAULT 0,
                notes TEXT,
                tomorrow_plan TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (date) REFERENCES daily_reviews(date)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS weekly_reviews (
                id TEXT PRIMARY KEY,
                week_start DATE NOT NULL,
                week_end DATE NOT NULL,
                goals_progress TEXT DEFAULT '{}',
                completed_habits INTEGER DEFAULT 0,
                total_habits INTEGER DEFAULT 0,
                habit_completion_rate REAL DEFAULT 0.0,
                productivity_trend TEXT,
                mood_trend TEXT,
                wins TEXT,
                challenges TEXT,
                next_week_focus TEXT,
                grade INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS grad_schedule (
                id TEXT PRIMARY KEY,
                day_of_week TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS accountability_log (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                trigger TEXT NOT NULL,
                message TEXT,
                action_taken TEXT,
                responded INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_goals_area ON goals(area_id)
        """)
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)
        """)
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_habits_active ON habits(is_active)
        """)
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_habit_logs_date ON habit_logs(date)
        """)
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_milestones_goal ON milestones(goal_id)
        """)

    def down(self, db) -> None:
        """Drop life management tables."""
        tables = [
            "accountability_log",
            "grad_schedule",
            "weekly_reviews",
            "daily_reviews",
            "habit_logs",
            "habits",
            "milestones",
            "goals",
            "user_profile",
            "life_areas",
        ]
        for table in tables:
            db.execute(f"DROP TABLE IF EXISTS {table}")


_MIGRATIONS = [
    LifeManagementMigration,
]
