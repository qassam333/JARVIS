"""JARVIS - Local Second Brain Assistant

A privacy-first, fully local AI assistant for task management,
scheduling, knowledge storage, and university integration.
"""

from jarvis.utils.config import config
from jarvis.utils.logger import setup_logger, get_logger


def main():
    """Main entry point."""
    setup_logger(level=config.log_level, debug=config.debug)

    logger = get_logger("main")
    logger.info(f"JARVIS v0.2.0 starting...")
    logger.info(f"Data directory: {config.data_dir}")
    logger.info(f"Database: {config.db_path}")

    config.ensure_directories()

    from jarvis.db.database import Database

    db = Database(config.db_path)
    db.initialize()

    logger.info("JARVIS is ready!")


if __name__ == "__main__":
    main()
