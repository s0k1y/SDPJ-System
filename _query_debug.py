import sqlite3

conn = sqlite3.connect(r'e:\Sky毕业设计\4.系统源代码\SDPJ-System\data\db\sdpj.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== All TaskGroups ===")
cursor.execute("SELECT * FROM TaskGroup")
for r in cursor.fetchall():
    print(f"  task_group_id={r['task_group_id']}, user_id={r['user_id']}, model_id={r['model_id']}")

print("\n=== All DetectionTasks ===")
cursor.execute("SELECT * FROM DetectionTask")
for r in cursor.fetchall():
    print(f"  task_id={r['task_id']}, task_group_id={r['task_group_id']}, dataset_id={r['dataset_id']}, status={r['task_status']}, algorithm={r['algorithm_type']}, start={r['start_time']}, end={r['end_time']}, error={r['error_message']}")

print("\n=== All DetectionReports ===")
cursor.execute("SELECT * FROM DetectionReport")
for r in cursor.fetchall():
    print(f"  report_id={r['report_id']}, task_id={r['task_id']}")

print("\n=== TaskGroup with task counts ===")
cursor.execute("""
    SELECT tg.task_group_id, tg.model_id, 
           COUNT(dt.task_id) as task_count,
           SUM(CASE WHEN dt.task_status = 'pending' THEN 1 ELSE 0 END) as pending,
           SUM(CASE WHEN dt.task_status = 'running' THEN 1 ELSE 0 END) as running,
           SUM(CASE WHEN dt.task_status = 'completed' THEN 1 ELSE 0 END) as completed,
           SUM(CASE WHEN dt.task_status = 'failed' THEN 1 ELSE 0 END) as failed,
           SUM(CASE WHEN dt.task_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
    FROM TaskGroup tg
    LEFT JOIN DetectionTask dt ON tg.task_group_id = dt.task_group_id
    GROUP BY tg.task_group_id
""")
for r in cursor.fetchall():
    print(f"  {r['task_group_id']} | model={r['model_id']} | total={r['task_count']} | pending={r['pending']} | running={r['running']} | completed={r['completed']} | failed={r['failed']} | cancelled={r['cancelled']}")

conn.close()
