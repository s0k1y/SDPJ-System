import sqlite3
import json

db_path = r"e:\Sky毕业设计\4.系统源代码\SDPJ-System\sdpj\infrastructure\database\sdpj.db"
conn = sqlite3.connect(db_path)

cur = conn.execute("PRAGMA table_info(PrivateConfig)")
cols = [r[1] for r in cur.fetchall()]
print("PrivateConfig columns:", cols)

cur2 = conn.execute("SELECT * FROM PrivateConfig LIMIT 5")
for row in cur2.fetchall():
    print(row[:3], "...")
    for i, c in enumerate(cols):
        if "content" in c.lower() or "config" in c.lower():
            val = row[i]
            if val:
                data = json.loads(val) if isinstance(val, str) else val
                result = data.get("multimodal_test_result", "NO RESULT") if isinstance(data, dict) else "NOT DICT"
                print(f"  {c}: multimodal_test_result={result}")

conn.close()
