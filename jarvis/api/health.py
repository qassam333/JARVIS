"""Health check endpoint."""

from datetime import datetime
from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Health check response model."""

    status: str
    database: str
    migrations: str
    timestamp: datetime


def check_health() -> HealthStatus:
    """
    Check system health.

    Returns:
        HealthStatus with component statuses
    """
    from jarvis.db.database import Database

    overall = "ok"
    db_status = "ok"
    migration_status = "ok"

    try:
        db = Database()

        with db.get_session() as conn:
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()

        with db.get_session() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM _migrations")
            row = cursor.fetchone()
            migration_count = row[0] if row else 0

            if migration_count == 0:
                migration_status = "not_initialized"
                overall = "degraded"

    except Exception as e:
        db_status = f"error: {str(e)}"
        overall = "degraded"

    return HealthStatus(
        status=overall,
        database=db_status,
        migrations=migration_status,
        timestamp=datetime.utcnow(),
    )
