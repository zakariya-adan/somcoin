from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

def db():
    return sqlite3.connect("pool.db")

@app.route("/api/stats")
def stats():
    con = db()
    cur = con.cursor()

    miners = cur.execute("SELECT COUNT(DISTINCT worker) FROM shares").fetchone()[0]
    total_shares = cur.execute("SELECT COUNT(*) FROM shares").fetchone()[0]
    paid = cur.execute("SELECT SUM(amount) FROM payouts").fetchone()[0] or 0

    con.close()

    return jsonify({
        "miners": miners,
        "shares": total_shares,
        "paid": round(paid, 4),
        "status": "online"
    })

@app.route("/api/miners")
def miners():
    con = db()
    cur = con.cursor()

    rows = cur.execute("""
    SELECT worker, COUNT(*) as shares
    FROM shares
    GROUP BY worker
    ORDER BY shares DESC
    LIMIT 20
    """).fetchall()

    con.close()

    return jsonify([
        {"worker": r[0], "shares": r[1]}
        for r in rows
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
