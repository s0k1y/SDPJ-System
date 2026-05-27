"""测试数据生成脚本 — 填充开发/测试用种子数据."""

import asyncio
from pathlib import Path


async def seed() -> None:  # noqa: D103
    from sdpj.infrastructure.database.result_db import (  # noqa: PLC0415
        SessionManager as ResultDBSessionManager,
    )
    from sdpj.infrastructure.database.sample_db import (  # noqa: PLC0415
        SampleDB,
        SampleDBSessionManager,
    )
    from sdpj.infrastructure.database.user_db import UserDBSessionManager  # noqa: PLC0415

    data_dir = Path(__file__).resolve().parents[2] / "database"  # noqa: ASYNC240
    data_dir.mkdir(parents=True, exist_ok=True)

    # 使用统一的数据库文件
    db_url = f"sqlite+aiosqlite:///{data_dir / 'sdpj.db'}"
    sample_sm = SampleDBSessionManager(db_url)
    result_sm = ResultDBSessionManager(db_url)
    user_sm = UserDBSessionManager(db_url)

    await sample_sm.create_tables()
    await result_sm.create_tables()
    await user_sm.create_tables()

    from sdpj.infrastructure.database.sample_db.builtin_datasets import (  # noqa: PLC0415
        load_builtin_datasets,
    )

    sample_db = SampleDB(sample_sm)
    await load_builtin_datasets(sample_db, force_reload=True)



def main() -> None:  # noqa: D103
    asyncio.run(seed())


if __name__ == "__main__":
    main()
