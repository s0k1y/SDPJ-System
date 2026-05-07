import asyncio
import sqlite3
import sys

sys.path.insert(0, r'E:\Sky毕业设计\4.系统源代码\SDPJ-System')

async def test():
    from sdpj.infrastructure.database.sample_db.session import SampleDBSessionManager
    from sdpj.infrastructure.database.sample_db.sample_db import SampleDB
    from sdpj.infrastructure.database.sample_db.builtin_datasets import load_builtin_datasets

    sm = SampleDBSessionManager()
    db = SampleDB(sm)
    await sm.initialize()

    conn = sqlite3.connect(r'E:\Sky毕业设计\4.系统源代码\SDPJ-System\data\db\sdpj.db')
    c = conn.cursor()
    c.execute("SELECT dataset_id, name FROM Dataset WHERE name LIKE '%jade_benchmark_medium_zh%'")
    ds = c.fetchall()
    print(f"Before: dataset_id={ds[0][0]}, name={ds[0][1]}")
    c.execute("SELECT COUNT(*) FROM DetectionSample WHERE dataset_id = ?", (ds[0][0],))
    print(f"Sample count before: {c.fetchone()[0]}")
    conn.close()

    print("Loading builtin datasets...")
    await load_builtin_datasets(db)

    conn = sqlite3.connect(r'E:\Sky毕业设计\4.系统源代码\SDPJ-System\data\db\sdpj.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM DetectionSample WHERE dataset_id = ?", (ds[0][0],))
    print(f"Sample count after: {c.fetchone()[0]}")
    conn.close()

    await sm.shutdown()

asyncio.run(test())
