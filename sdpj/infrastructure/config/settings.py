"""全局配置 — 基于 pydantic-settings，从环境变量 / .env 文件加载"""
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from sdpj.infrastructure.config.constants import (
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
    import secrets
    key = secrets.token_hex(SECRET_KEY_BYTES)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(key)
    return key


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["development", "test", "production"] = "development"
    debug: bool = True
    sample_db_url: str = "sqlite+aiosqlite:///./data/db/sample.db"
    result_db_url: str = "sqlite+aiosqlite:///./data/db/result.db"
    user_db_url: str = "sqlite+aiosqlite:///./data/db/user.db"
    secret_key: str = ""
    adapters_dir: str = "~/.sdpj/adapters/"
    log_level: str = "INFO"
    log_dir: str = f"./{DEFAULT_LOG_DIR}"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    def resolve_secret_key(self) -> str:
        if self.secret_key:
            return self.secret_key
        return _load_or_generate_secret_key()

    def resolve_adapters_dir(self) -> Path:
        return Path(self.adapters_dir).expanduser().resolve()


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
