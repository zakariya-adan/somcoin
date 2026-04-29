import sqlite3

con = sqlite3.connect("pool.db")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    address TEXT PRIMARY KEY,
    balance REAL DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker TEXT,
    diff INTEGER,
    time INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS payouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT,
    amount REAL,
    time INTEGER
)
""")

con.commit()
con.close()

print("✅ DATABASE CREATED")
