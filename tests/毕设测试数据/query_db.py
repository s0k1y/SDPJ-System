import sqlite3
import json

db_path = r"e:\Sky毕业设计\4.系统源代码\SDPJ-System\sdpj\infrastructure\database\sdpj.db"
conn = sqlite3.connect(db_path)
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

for t in tables:
    if "config" in t.lower() or "private" in t.lower() or "resource" in t.lower():
        cur2 = conn.execute(f"SELECT * FROM {t} LIMIT 5")
        cols = [d[0] for d in cur2.description]
        print(f"\n--- {t} ({', '.join(cols)}) ---")
        for row in cur2.fetchall():
            print(row)

conn.close()
