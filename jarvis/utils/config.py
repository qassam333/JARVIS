"""Configuration management with environment variable support."""

import os
import sys
from pathlib import Path
from typing import Any, Optional
from functools import lru_cache

import yaml
from pydantic import BaseModel, Field, field_validator


class JarvisCore(BaseModel):
    name: str = "JARVIS"
    version: str = "0.2.0"
    data_dir: Path = Path(__file__).resolve().parent.parent.parent / "data"
    database: str = "jarvis.db"
    debug: bool = False


class JarvisUser(BaseModel):
    name: Optional[str] = None
    timezone: str = "UTC"
    preferences: dict[str, Any] = {}


class JarvisUniversity(BaseModel):
    enabled: bool = False
    auto_sync: bool = False
    sync_time: str = "06:00"
    services: list[str] = []


class JarvisVoice(BaseModel):
    enabled: bool = False
    wake_word: str = "hey jarvis"
    stt_model: str = "base"
    tts_voice: str = "en_US-lessac-medium"


class JarvisPrivacy(BaseModel):
    encrypted: bool = True
    log_level: str = "info"
    telemetry: bool = False


class JarvisAPI(BaseModel):
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]


class JarvisDatabase(BaseModel):
    path: Optional[Path] = None
    backup_dir: Path = Path("./backups")


class JarvisConfigModel(BaseModel):
    jarvis: JarvisCore = JarvisCore()
    user: JarvisUser = JarvisUser()
    university: JarvisUniversity = JarvisUniversity()
    voice: JarvisVoice = JarvisVoice()
    privacy: JarvisPrivacy = JarvisPrivacy()
    api: JarvisAPI = JarvisAPI()
    database: JarvisDatabase = JarvisDatabase()


def _load_env_file() -> None:
    """Load .env file if present."""
    env_path = Path(".env")

    if not env_path.exists():
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key not in os.environ:
                    os.environ[key] = value


def _get_env_bool(value: str) -> bool:
    """Convert string to boolean."""
    return value.lower() in ("true", "1", "yes", "on")


def _resolve_config_from_env(config: JarvisConfigModel) -> JarvisConfigModel:
    """Override config with environment variables."""

    # Core settings
    if debug := os.environ.get("JARVIS_DEBUG"):
        config.jarvis.debug = _get_env_bool(debug)

    if data_dir := os.environ.get("JARVIS_DATA_DIR"):
        config.jarvis.data_dir = Path(data_dir)

    if db_path := os.environ.get("JARVIS_DB_PATH"):
        config.database.path = Path(db_path)

    # Logging
    if log_level := os.environ.get("JARVIS_LOG_LEVEL"):
        config.privacy.log_level = log_level.lower()

    # University
    if uni_enabled := os.environ.get("JARVIS_UNIVERSITY_ENABLED"):
        config.university.enabled = _get_env_bool(uni_enabled)

    if uni_sync := os.environ.get("JARVIS_UNIVERSITY_AUTO_SYNC"):
        config.university.auto_sync = _get_env_bool(uni_sync)

    # Voice
    if voice_enabled := os.environ.get("JARVIS_VOICE_ENABLED"):
        config.voice.enabled = _get_env_bool(voice_enabled)

    if wake_word := os.environ.get("JARVIS_VOICE_WAKE_WORD"):
        config.voice.wake_word = wake_word.lower()

    if stt_model := os.environ.get("JARVIS_VOICE_STT_MODEL"):
        config.voice.stt_model = stt_model

    # API
    if api_enabled := os.environ.get("JARVIS_API_ENABLED"):
        config.api.enabled = _get_env_bool(api_enabled)

    if api_host := os.environ.get("JARVIS_API_HOST"):
        config.api.host = api_host

    if api_port := os.environ.get("JARVIS_API_PORT"):
        config.api.port = int(api_port)

    # User
    if user_name := os.environ.get("JARVIS_USER_NAME"):
        config.user.name = user_name

    if user_tz := os.environ.get("JARVIS_USER_TIMEZONE"):
        config.user.timezone = user_tz

    # Security
    if master_key := os.environ.get("JARVIS_MASTER_KEY"):
        os.environ["JARVIS__MASTER_KEY"] = master_key

    return config


@lru_cache()
def _load_config() -> JarvisConfigModel:
    """Load configuration from file and environment."""

    # Load .env first
    _load_env_file()

    # Default config
    config = JarvisConfigModel()

    # Load from config.yaml
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config:
                if "jarvis" in yaml_config:
                    if "data_dir" in yaml_config["jarvis"]:
                        config.jarvis.data_dir = Path(yaml_config["jarvis"]["data_dir"])
                    if "database" in yaml_config["jarvis"]:
                        config.jarvis.database = yaml_config["jarvis"]["database"]
                    if "debug" in yaml_config["jarvis"]:
                        config.jarvis.debug = yaml_config["jarvis"]["debug"]

                if "user" in yaml_config:
                    config.user = JarvisUser(**yaml_config["user"])

                if "university" in yaml_config:
                    config.university = JarvisUniversity(**yaml_config["university"])

                if "voice" in yaml_config:
                    config.voice = JarvisVoice(**yaml_config["voice"])

                if "privacy" in yaml_config:
                    config.privacy = JarvisPrivacy(**yaml_config["privacy"])

                if "api" in yaml_config:
                    config.api = JarvisAPI(**yaml_config["api"])

    # Override with environment variables
    config = _resolve_config_from_env(config)

    # Resolve paths
    if config.database.path is None:
        config.database.path = config.jarvis.data_dir / config.jarvis.database

    return config


class Config:
    """Configuration wrapper for easy access."""

    def __init__(self):
        self._config = _load_config()

    @property
    def debug(self) -> bool:
        return self._config.jarvis.debug

    @property
    def data_dir(self) -> Path:
        return self._config.jarvis.data_dir

    @property
    def db_path(self) -> Path:
        return self._config.database.path

    @property
    def log_level(self) -> str:
        return self._config.privacy.log_level

    @property
    def user_name(self) -> Optional[str]:
        return self._config.user.name

    @property
    def timezone(self) -> str:
        return self._config.user.timezone

    @property
    def university_enabled(self) -> bool:
        return self._config.university.enabled

    @property
    def university_auto_sync(self) -> bool:
        return self._config.university.auto_sync

    @property
    def voice_enabled(self) -> bool:
        return self._config.voice.enabled

    @property
    def wake_word(self) -> str:
        return self._config.voice.wake_word

    @property
    def api_enabled(self) -> bool:
        return self._config.api.enabled

    @property
    def api_host(self) -> str:
        return self._config.api.host

    @property
    def api_port(self) -> int:
        return self._config.api.port

    def ensure_directories(self) -> None:
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def reload(self) -> None:
        """Reload configuration from disk.

        Clears the lru_cache so _load_config() runs fresh.
        """
        _load_config.cache_clear()
        self._config = _load_config()

    def to_dict(self) -> dict[str, Any]:
        """Export configuration as dictionary."""
        return self._config.model_dump()


config = Config()
