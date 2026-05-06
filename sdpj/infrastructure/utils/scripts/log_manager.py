"""日志管理工具

提供日志查询、统计和清理功能。
"""
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path


async def show_log_stats():
    """显示日志统计信息"""
    from sdpj.infrastructure.database.result_db import ResultDB, SessionManager

    data_dir = Path(__file__).resolve().parents[1] / "data" / "db"
    db_url = f"sqlite+aiosqlite:///{data_dir / 'sdpj.db'}"
    session_manager = SessionManager(db_url)
    result_db = ResultDB(session_manager)

    # 查询所有日志
    all_logs = await result_db.query_logs(limit=10000)

    print("=" * 60)
    print("System Log Statistics")
    print("=" * 60)
    print(f"Total logs: {len(all_logs)}")

    # 按类别统计
    category_counts = {}
    level_counts = {}
    for log in all_logs:
        category = log["category"]
        level = log["level"]
        category_counts[category] = category_counts.get(category, 0) + 1
        level_counts[level] = level_counts.get(level, 0) + 1

    print("\nBy Category:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count}")

    print("\nBy Level:")
    for level, count in sorted(level_counts.items()):
        print(f"  {level}: {count}")

    # 最近的日志
    print("\nRecent logs (last 5):")
    for log in all_logs[:5]:
        print(f"  [{log['timestamp']}] {log['category']} - {log['description'][:50]}")

    print("=" * 60)


async def clean_old_logs(days: int = 30):
    """清理指定天数之前的日志

    Args:
        days: 保留最近多少天的日志，默认 30 天
    """
    from sdpj.infrastructure.database.result_db import ResultDB, SessionManager

    data_dir = Path(__file__).resolve().parents[1] / "data" / "db"
    db_url = f"sqlite+aiosqlite:///{data_dir / 'sdpj.db'}"
    session_manager = SessionManager(db_url)
    result_db = ResultDB(session_manager)

    before = datetime.now(timezone.utc) - timedelta(days=days)
    deleted_count = await result_db.delete_old_logs(before)

    print(f"Deleted {deleted_count} logs older than {days} days")


async def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m sdpj.infrastructure.utils.scripts.log_manager stats")
        print("  python -m sdpj.infrastructure.utils.scripts.log_manager clean [days]")
        return

    command = sys.argv[1]

    if command == "stats":
        await show_log_stats()
    elif command == "clean":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        await clean_old_logs(days)
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
