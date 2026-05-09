"""数据库迁移脚本 - 添加系统日志表"""

import asyncio
from pathlib import Path


async def migrate():
    from sdpj.infrastructure.database.result_db import SessionManager

    data_dir = Path(__file__).resolve().parents[2] / "database"
    data_dir.mkdir(parents=True, exist_ok=True)

    db_url = f"sqlite+aiosqlite:///{data_dir / 'sdpj.db'}"
    session_manager = SessionManager(db_url)

    # 创建日志表
    await session_manager.create_tables()

    print("System log table created successfully")


if __name__ == "__main__":
    asyncio.run(migrate())
