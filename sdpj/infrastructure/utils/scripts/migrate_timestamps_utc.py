"""数据库迁移脚本 - 统一时间戳为UTC-naive格式.

旧日志使用本地时间(naive datetime)存储,新日志使用UTC时间(aware datetime)存储.
此脚本将所有时间戳统一为UTC-naive格式,确保排序正确.

迁移逻辑:
1. 有时区后缀的记录(如 "+00:00"):转为UTC后去掉时区信息
2. 无时区后缀的记录:视为本地时间,根据系统时区偏移转为UTC后去掉时区信息
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path


async def migrate_timestamps_to_utc() -> None:  # noqa: C901, D103, PLR0912, PLR0915
    from sdpj.infrastructure.database.result_db import SessionManager  # noqa: PLC0415

    data_dir = Path(__file__).resolve().parents[2] / "database"  # noqa: ASYNC240
    db_url = f"sqlite+aiosqlite:///{data_dir / 'sdpj.db'}"
    session_manager = SessionManager(db_url)
    await session_manager.initialize()

    local_offset = datetime.now().astimezone().utcoffset()
    _offset_hours = local_offset.total_seconds() / 3600 if local_offset else 0

    if session_manager.engine is None:
        return

    async with session_manager.engine.begin() as conn:
        result = await conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='SystemLog'",
        )
        if not result.fetchall():
            return

        result = await conn.exec_driver_sql("SELECT COUNT(*) FROM SystemLog")
        row = result.fetchone()
        if row is None:
            return
        total = row[0]
        if total == 0:
            return


        result = await conn.exec_driver_sql("SELECT log_id, timestamp FROM SystemLog")
        rows = result.fetchall()

        migrated = 0
        for row in rows:
            log_id = row[0]
            ts_str = row[1]

            if ts_str is None:
                continue

            if isinstance(ts_str, str) and ("+" in ts_str[10:] or ts_str.endswith("Z")):
                try:
                    dt = datetime.fromisoformat(ts_str)
                    utc_naive = dt.astimezone(UTC).replace(tzinfo=None)
                    new_str = utc_naive.strftime("%Y-%m-%d %H:%M:%S.%f")
                    await conn.exec_driver_sql(
                        "UPDATE SystemLog SET timestamp = ? WHERE log_id = ?",
                        (new_str, log_id),
                    )
                    migrated += 1
                except (ValueError, OverflowError):
                    pass
            else:
                try:
                    dt = datetime.fromisoformat(ts_str) if isinstance(ts_str, str) else ts_str

                    if dt.tzinfo is not None:
                        utc_naive = dt.astimezone(UTC).replace(tzinfo=None)
                    elif local_offset is not None:
                        utc_naive = dt - local_offset
                    else:
                        utc_naive = dt

                    new_str = utc_naive.strftime("%Y-%m-%d %H:%M:%S.%f")
                    await conn.exec_driver_sql(
                        "UPDATE SystemLog SET timestamp = ? WHERE log_id = ?",
                        (new_str, log_id),
                    )
                    migrated += 1
                except (ValueError, OverflowError):
                    pass


        result = await conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='DetectionTask'",
        )
        if result.fetchall():
            result = await conn.exec_driver_sql(
                "SELECT task_id, start_time, end_time FROM DetectionTask",
            )
            task_rows = result.fetchall()
            task_migrated = 0
            for row in task_rows:
                task_id = row[0]
                updates = {}
                for idx, col in enumerate(["start_time", "end_time"]):
                    ts_str = row[idx + 1]
                    if ts_str is None:
                        continue
                    try:
                        if isinstance(ts_str, str) and ("+" in ts_str[10:] or ts_str.endswith("Z")):
                            dt = datetime.fromisoformat(ts_str)
                            utc_naive = dt.astimezone(UTC).replace(tzinfo=None)
                        elif isinstance(ts_str, str):
                            dt = datetime.fromisoformat(ts_str)
                            if dt.tzinfo is not None:
                                utc_naive = dt.astimezone(UTC).replace(tzinfo=None)
                            elif local_offset is not None:
                                utc_naive = dt - local_offset
                            else:
                                utc_naive = dt
                        else:
                            dt = ts_str
                            if dt.tzinfo is not None:
                                utc_naive = dt.astimezone(UTC).replace(tzinfo=None)
                            elif local_offset is not None:
                                utc_naive = dt - local_offset
                            else:
                                utc_naive = dt
                        updates[col] = utc_naive.strftime("%Y-%m-%d %H:%M:%S.%f")
                    except (ValueError, OverflowError):
                        pass

                if updates:
                    set_clause = ", ".join(f"{k} = ?" for k in updates)
                    values = [*list(updates.values()), task_id]
                    await conn.exec_driver_sql(
                        f"UPDATE DetectionTask SET {set_clause} WHERE task_id = ?",  # noqa: S608
                        values,
                    )
                    task_migrated += 1


    await session_manager.close()


if __name__ == "__main__":
    asyncio.run(migrate_timestamps_to_utc())
