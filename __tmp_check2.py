import sqlite3, json

conn = sqlite3.connect(r'E:\Sky毕业设计\4.系统源代码\SDPJ-System\data\db\sdpj.db')
c = conn.cursor()

c.execute("SELECT dataset_id, name FROM Dataset WHERE name LIKE '%jade_benchmark_medium_zh%'")
ds = c.fetchall()
print(f"Datasets: {ds}")

if ds:
    did = ds[0][0]
    c.execute("SELECT COUNT(*) FROM DetectionSample WHERE dataset_id = ?", (did,))
    count = c.fetchone()[0]
    print(f"Sample count: {count}")

conn.close()

with open(r'E:\Sky毕业设计\4.系统源代码\SDPJ-System\sdpj\infrastructure\database\sample_db\builtin_datasets\__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'file_line_count' in content:
        print("New code IS present in __init__.py")
    else:
        print("Old code still in __init__.py - fix not applied or not saved")
