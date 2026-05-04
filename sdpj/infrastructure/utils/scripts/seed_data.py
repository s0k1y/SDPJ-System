"""测试数据生成脚本 — 填充开发/测试用种子数据"""
import asyncio
import sys
from pathlib import Path


async def seed() -> None:
    from sdpj.infrastructure.database.sample_db import SampleDB, SampleDBSessionManager
    from sdpj.infrastructure.database.result_db import ResultDB, SessionManager as ResultDBSessionManager
    from sdpj.infrastructure.database.user_db import UserDB, UserDBSessionManager

    data_dir = Path(__file__).resolve().parents[4] / "data" / "db"
    data_dir.mkdir(parents=True, exist_ok=True)

    sample_sm = SampleDBSessionManager()
    result_sm = ResultDBSessionManager(f"sqlite+aiosqlite:///{data_dir / 'sdpj_results.db'}")
    user_sm = UserDBSessionManager(f"sqlite+aiosqlite:///{data_dir / 'sdpj_users.db'}")

    await sample_sm.create_tables()
    await result_sm.create_tables()
    await user_sm.create_tables()

    from sdpj.infrastructure.database.sample_db.builtin_datasets import load_builtin_datasets
    sample_db = SampleDB(sample_sm)
    await load_builtin_datasets(sample_db)

    print("Database tables created and builtin datasets loaded.")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
