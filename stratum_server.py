from pool import save_share, distribute_reward, payout, init
import socket, threading, json, time, hashlib, requests, random, sqlite3

# ================= CONFIG =================
HOST = "0.0.0.0"
PORT = 3333

NODE = "http://127.0.0.1:9443"
POOL_WALLET = "SOM2c6c6c5d9412a112ff10f749b40407a986"

START_DIFF = 2
MIN_PAYOUT = 1

clients = {}
jobs = {}
submitted = set()
found_blocks = set()

lock = threading.Lock()
last_job = None

# ================= HASH =================
def pow_hash(data):
    return hashlib.scrypt(
        data.encode(),
        salt=b"somcoin",
        n=1024,
        r=1,
        p=1
    ).hex()

# ================= TARGET =================
def check_target(h, diff):
    max_target = int("f"*64, 16)
    target = max_target // (diff * 1000)
    return int(h, 16) < target

# ================= SAFE GET =================
def safe_get(url):
    try:
        return requests.get(url, timeout=5).json()
    except:
        return None

# ================= SEND =================
def send(conn, data):
    try:
        conn.send((json.dumps(data) + "\n").encode())
    except:
        pass

# ================= JOB =================
def get_job():
    return safe_get(f"{NODE}/get_block_template")

def broadcast(job):
    for w, c in list(clients.items()):
        send(c["conn"], {
            "id": None,
            "method": "mining.notify",
            "params": [
                job["job_id"],
                job["index"],
                job["prev_hash"],
                job["merkle_root"],
                job["timestamp"],
                True
            ]
        })

# ================= CLIENT =================
def handle(conn, addr):
    worker = None
    extranonce = str(random.randint(100000, 999999))
    buffer = ""

    print("👷 Miner connected:", addr)

    while True:
        try:
            raw = conn.recv(4096)
            if not raw:
                break

            data = raw.decode("utf-8", errors="ignore")

            buffer += data

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                if not line.strip():
                    continue

                try:
                    msg = json.loads(line)
                except:
                    continue

                method = msg.get("method")

                # ================= SUBSCRIBE =================
                if method == "mining.subscribe":
                    send(conn, {
                        "id": msg.get("id"),
                        "result": [["mining.set_difficulty", "1"], extranonce],
                        "error": None
                    })

                    # 🔥 SEND DIFF
                    send(conn, {
                        "id": None,
                        "method": "mining.set_difficulty",
                        "params": [START_DIFF]
                    })

                # ================= AUTHORIZE =================
                elif method == "mining.authorize":
                    worker = msg["params"][0]

                    with lock:
                        clients[worker] = {
                            "conn": conn,
                            "diff": START_DIFF,
                            "shares": 0,
                            "last": time.time()
                        }

                    send(conn, {
                        "id": msg.get("id"),
                        "result": True,
                        "error": None
                    })

                # ================= SUBMIT =================
                elif method == "mining.submit":

                    try:
                        w = msg["params"][0]
                        jid = msg["params"][1]
                        nonce = msg["params"][2]
                    except:
                        continue

                    job = jobs.get(jid)
                    if not job:
                        continue

                    key = f"{w}-{jid}-{nonce}"
                    if key in submitted:
                        continue
                    submitted.add(key)

                    header = (
                        str(job["index"]) +
                        job["prev_hash"] +
                        str(job["timestamp"]) +
                        job["merkle_root"] +
                        str(nonce)
                    )

                    h = pow_hash(header)

                    client = clients.get(w)
                    if not client:
                        continue

                    # ================= SHARE =================
                    if check_target(h, client["diff"]):

                        client["shares"] += 1
                        client["last"] = time.time()

                        save_share(w, client["diff"])

                        send(conn, {
                            "id": msg.get("id"),
                            "result": True,
                            "error": None
                        })

                        print("⚡ Share:", w)

                    else:
                        send(conn, {
                            "id": msg.get("id"),
                            "result": False,
                            "error": "low diff"
                        })
                        continue

                    # ================= BLOCK =================
                    if check_target(h, job["difficulty"] * 1000):

                        if jid in found_blocks:
                            continue

                        found_blocks.add(jid)

                        print("🔥 BLOCK FOUND:", w)

                        res = safe_get(f"{NODE}/mine/{POOL_WALLET}")

                        if res and "reward" in res:
                            distribute_reward(res["reward"])

        except Exception as e:
            print("ERR:", e)
            break

    conn.close()

    if worker:
        with lock:
            clients.pop(worker, None)

# ================= JOB LOOP =================
def job_loop():
    global last_job

    while True:
        job = get_job()

        if job and "index" in job:
            jid = str(job["index"])

            if jid != last_job:
                last_job = jid
                job["job_id"] = jid
                jobs[jid] = job

                print(f"📦 New Job {jid}")
                broadcast(job)

        time.sleep(2)

# ================= PAYOUT =================
def payout_loop():
    while True:
        time.sleep(20)

        try:
            con = sqlite3.connect("pool.db")
            cur = con.cursor()

            users = cur.execute("SELECT address,balance FROM users").fetchall()
            con.close()

            for addr, bal in users:
                if bal >= MIN_PAYOUT:
                    payout(addr, bal, NODE, POOL_WALLET)

        except Exception as e:
            print("Payout error:", e)

# ================= START =================
def start():
    init()

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(100)

    print("🚀 STRATUM PRO RUNNING ON 3333")

    threading.Thread(target=job_loop, daemon=True).start()
    threading.Thread(target=payout_loop, daemon=True).start()

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start()
