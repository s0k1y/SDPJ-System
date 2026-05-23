import sqlite3

db = sqlite3.connect("sdpj/infrastructure/database/sdpj.db")
# Users
rows = db.execute("SELECT user_id, username, created_at FROM User").fetchall()
print("Users:", len(rows))
for r in rows:
    print(" ", r)
# PrivateConfig
rows = db.execute("SELECT * FROM PrivateConfig").fetchall()
print("PrivateConfig:", len(rows))
# Resource
rows = db.execute("SELECT * FROM Resource").fetchall()
print("Resource:", len(rows))
for r in rows:
    print(" ", r)
