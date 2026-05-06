import sqlite3
conn = sqlite3.connect("data/db/sdpj.db")
cursor = conn.execute("SELECT task_id, task_status, start_time, end_time FROM DetectionTask ORDER BY rowid DESC LIMIT 3")
for row in cursor.fetchall():
    print(f"Task {row[0]}: status={row[1]}, start={row[2]}, end={row[3]}")
conn.close()
