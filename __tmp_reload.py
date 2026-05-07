import asyncio
import sqlite3
import sys
import os

os.chdir(r'E:\Sky毕业设计\4.系统源代码\SDPJ-System')
sys.path.insert(0, r'E:\Sky毕业设计\4.系统源代码\SDPJ-System')

async def main():
    from sdpj.infrastructure.database.sample_db.session import SampleDBSessionManager
    from sdpj.infrastructure.database.sample_db.sample_db import SampleDB
    from sdpj.infrastructure.database.sample_db.builtin_datasets import load_builtin_datasets

    sm = SampleDBSessionManager()
    db = SampleDB(sm)
    await sm.initialize()

    print("Loading builtin datasets...")
    await load_builtin_datasets(db)

    conn = sqlite3.connect(r'E:\Sky毕业设计\4.系统源代码\SDPJ-System\data\db\sdpj.db')
    c = conn.cursor()
    c.execute("SELECT dataset_id, name FROM Dataset WHERE name LIKE '%jade_benchmark_medium_zh%'")
    ds = c.fetchall()
    if ds:
        c.execute("SELECT COUNT(*) FROM DetectionSample WHERE dataset_id = ?", (ds[0][0],))
        print(f"jade_benchmark_medium_zh: {c.fetchone()[0]} samples")
    conn.close()

    await sm.shutdown()

asyncio.run(main())
