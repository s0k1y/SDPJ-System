import sqlite3

DB = r"e:\Sky毕业设计\4.系统源代码\SDPJ-System\data\db\sdpj.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=== Users ===")
c.execute("SELECT * FROM User")
for r in c.fetchall():
    print(dict(r))

print("\n=== AccessControl ===")
c.execute("SELECT * FROM AccessControl")
for r in c.fetchall():
    print(dict(r))

print("\n=== PrivateConfig ===")
c.execute("SELECT * FROM PrivateConfig")
for r in c.fetchall():
    print(dict(r))

print("\n=== Resource ===")
c.execute("SELECT * FROM Resource")
for r in c.fetchall():
    print(dict(r))

conn.close()
