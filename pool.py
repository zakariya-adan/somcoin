import sqlite3, time

DB = "pool.db"
POOL_FEE = 0.02

def db():
    return sqlite3.connect(DB)

def init():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        address TEXT PRIMARY KEY,
        balance REAL DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shares(
        worker TEXT,
        diff INTEGER,
        time INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payouts(
        address TEXT,
        amount REAL,
        time INTEGER
    )
    """)

    con.commit()
    con.close()

def save_share(worker, diff):
    con = db()
    cur = con.cursor()

    cur.execute("INSERT INTO shares VALUES(?,?,?)",
        (worker, diff, int(time.time()))
    )

    con.commit()
    con.close()

def add_balance(addr, amount):
    con = db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO users(address,balance)
    VALUES(?,?)
    ON CONFLICT(address)
    DO UPDATE SET balance = balance + ?
    """, (addr, amount, amount))

    con.commit()
    con.close()

def distribute_reward(reward):
    con = db()
    cur = con.cursor()

    shares = cur.execute("SELECT worker, COUNT(*) FROM shares GROUP BY worker").fetchall()
    total = sum(s[1] for s in shares)

    if total == 0:
        return

    reward = reward * (1 - POOL_FEE)

    for worker, count in shares:
        part = count / total
        add_balance(worker, reward * part)

    cur.execute("DELETE FROM shares")
    con.commit()
    con.close()

def payout(addr, amount, node_url, pool_wallet):
    import requests

    res = requests.post(f"{node_url}/send", json={
        "from": pool_wallet,
        "to": addr,
        "amount": round(amount, 8),
        "fee": 0.01
    }).json()

    if "status" in res:
        con = db()
        cur = con.cursor()

        cur.execute("UPDATE users SET balance=0 WHERE address=?", (addr,))
        cur.execute("INSERT INTO payouts VALUES(?,?,?)", (addr, amount, int(time.time())))

        con.commit()
        con.close()

        print("💸 Paid:", addr)
