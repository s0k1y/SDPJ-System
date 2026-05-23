"""CLI 会话持久化模块

将登录状态持久化到本地 JSON 文件，使 CLI 跨命令保持登录态。
文件路径: sdpj/ui/cli/session.json（相对于项目根目录）
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

_SESSION_FILE = Path(__file__).resolve().parent / "session.json"
_SESSION_TTL = timedelta(hours=24)


def save_session(user_id: int) -> None:
    _SESSION_FILE.write_text(
        json.dumps(
            {"user_id": user_id, "logged_in_at": datetime.now(timezone.utc).isoformat()},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def load_session() -> int | None:
    if not _SESSION_FILE.exists():
        return None
    try:
        data = json.loads(_SESSION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    user_id = data.get("user_id")
    logged_in_at = data.get("logged_in_at")
    if not isinstance(user_id, int) or not isinstance(logged_in_at, str):
        return None
    try:
        ts = datetime.fromisoformat(logged_in_at)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - ts > _SESSION_TTL:
            clear_session()
            return None
    except (ValueError, TypeError):
        clear_session()
        return None
    return user_id


def clear_session() -> None:
    try:
        _SESSION_FILE.unlink()
    except FileNotFoundError:
        pass
