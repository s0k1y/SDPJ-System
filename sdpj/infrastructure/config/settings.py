"""全局配置 — 基于 pydantic-settings,从环境变量 / .env 文件加载."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from sdpj.infrastructure.config.constants import (
    DEFAULT_EXPORT_DIR,
    DEFAULT_LOG_DIR,
    SECRET_KEY_BYTES,
    SECRET_KEY_FILENAME,
    USER_CONFIG_DIR_NAME,
)


def _user_config_dir() -> Path:
    return Path.home() / USER_CONFIG_DIR_NAME


def _load_or_generate_secret_key() -> str:
    key_path = _user_config_dir() / SECRET_KEY_FILENAME
    if key_path.exists():
        return key_path.read_text().strip()
    import secrets  # noqa: PLC0415

    key = secrets.token_hex(SECRET_KEY_BYTES)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(key)
    return key


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _default_db_url() -> str:
    db_path = _PROJECT_ROOT / "sdpj" / "infrastructure" / "database" / "sdpj.db"
    return f"sqlite+aiosqlite:///{db_path}"


class Settings(BaseSettings):  # noqa: D101
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["development", "test", "production"] = "development"
    debug: bool = True
    db_url: str = _default_db_url()
    secret_key: str = ""
    adapters_dir: str = "~/.sdpj/adapters/"
    log_level: str = "INFO"
    log_dir: str = str(_PROJECT_ROOT / DEFAULT_LOG_DIR)
    export_dir: str = str(_PROJECT_ROOT / DEFAULT_EXPORT_DIR)
    api_host: str = "0.0.0.0"  # noqa: S104
    api_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    def resolve_secret_key(self) -> str:  # noqa: D102
        if self.secret_key:
            return self.secret_key
        return _load_or_generate_secret_key()

    def resolve_adapters_dir(self) -> Path:  # noqa: D102
        return Path(self.adapters_dir).expanduser().resolve()


_settings: Settings | None = None


def get_settings() -> Settings:  # noqa: D103
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = Settings()
    return _settings
