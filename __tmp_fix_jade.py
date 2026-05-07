import sqlite3

DB_PATH = r'E:\Sky毕业设计\4.系统源代码\SDPJ-System\data\db\sdpj.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("SELECT dataset_id, name FROM Dataset WHERE name LIKE '%jade_benchmark_medium_zh%'")
ds = c.fetchall()
if not ds:
    print("Dataset not found!")
    conn.close()
    exit()

did = ds[0][0]
name = ds[0][1]
print(f"Dataset: id={did}, name={name}")

c.execute("SELECT COUNT(*) FROM DetectionSample WHERE dataset_id = ?", (did,))
before = c.fetchone()[0]
print(f"Samples before delete: {before}")

c.execute("DELETE FROM DetectionSample WHERE dataset_id = ?", (did,))
deleted = c.rowcount
conn.commit()
print(f"Deleted: {deleted}")

c.execute("SELECT COUNT(*) FROM DetectionSample WHERE dataset_id = ?", (did,))
after = c.fetchone()[0]
print(f"Samples after delete: {after}")

conn.close()
print("\nNow restart the system to reload all builtin datasets from files.")
