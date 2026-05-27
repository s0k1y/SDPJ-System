"""日志管理工具.

提供日志查询,统计和清理功能.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path


async def show_log_stats() -> None:
    """显示日志统计信息."""
    from sdpj.infrastructure.database.result_db import ResultDB, SessionManager  # noqa: PLC0415

    data_dir = Path(__file__).resolve().parents[2] / "database"  # noqa: ASYNC240
    db_url = f"sqlite+aiosqlite:///{data_dir / 'sdpj.db'}"
    session_manager = SessionManager(db_url)
    result_db = ResultDB(session_manager)

    # 查询所有日志
    all_logs = await result_db.query_logs(limit=10000)


    # 按类别统计
    category_counts: dict[str, int] = {}
    level_counts: dict[str, int] = {}
    for log in all_logs:
        category = log["category"]
        level = log["level"]
        category_counts[category] = category_counts.get(category, 0) + 1
        level_counts[level] = level_counts.get(level, 0) + 1

    for category, _count in sorted(category_counts.items()):  # noqa: B007
        pass

    for level, _count in sorted(level_counts.items()):  # noqa: B007
        pass

    # 最近的日志
    for log in all_logs[:5]:  # noqa: B007
        pass



async def clean_old_logs(days: int = 30) -> None:
    """清理指定天数之前的日志.

    Args:
        days: 保留最近多少天的日志,默认 30 天

    """
    from sdpj.infrastructure.database.result_db import ResultDB, SessionManager  # noqa: PLC0415

    data_dir = Path(__file__).resolve().parents[2] / "database"  # noqa: ASYNC240
    db_url = f"sqlite+aiosqlite:///{data_dir / 'sdpj.db'}"
    session_manager = SessionManager(db_url)
    result_db = ResultDB(session_manager)

    before = datetime.now(UTC) - timedelta(days=days)
    await result_db.delete_old_logs(before)



async def main() -> None:  # noqa: D103
    import sys  # noqa: PLC0415

    if len(sys.argv) < 2:  # noqa: PLR2004
        return

    command = sys.argv[1]

    if command == "stats":
        await show_log_stats()
    elif command == "clean":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30  # noqa: PLR2004
        await clean_old_logs(days)
    else:
        pass


if __name__ == "__main__":
    asyncio.run(main())
