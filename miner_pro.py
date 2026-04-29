import socket, json, time, hashlib, random, threading

POOL = "167.86.117.249"
PORT = 3333

WALLET = "SOMhD4R0RPoYIJ5bzv7STpokScDRi2zrv"

job = None
diff = 2

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

# ================= CONNECT =================
def connect():
    while True:
        try:
            s = socket.socket()
            s.connect((POOL, PORT))
            print("✅ Connected")
            return s
        except:
            time.sleep(3)

# ================= SEND =================
def send(s, data):
    s.send((json.dumps(data)+"\n").encode())

# ================= LISTEN =================
def listen(s):
    global job, diff

    buffer = ""

    while True:
        data = s.recv(4096).decode(errors="ignore")
        if not data:
            break

        buffer += data

        while "\n" in buffer:
            line, buffer = buffer.split("\n",1)

            try:
                msg = json.loads(line)
            except:
                continue

            if msg.get("method") == "mining.notify":
                p = msg["params"]

                job = {
                    "id": p[0],
                    "index": p[1],
                    "prev": p[2],
                    "root": p[3],
                    "time": p[4]
                }

                print("📦 Job", job["id"])

            elif msg.get("method") == "mining.set_difficulty":
                diff = msg["params"][0]
                print("⚙️ Diff:", diff)

# ================= MINER =================
def mine(s):
    global job, diff

    while True:
        if not job:
            time.sleep(1)
            continue

        j = job

        base = (
            str(j["index"]) +
            j["prev"] +
            str(j["time"]) +
            j["root"]
        )

        while job == j:
            nonce = random.randint(0, 2**32)

            h = pow_hash(base + str(nonce))

            if check_target(h, diff):
                print("⚡ SHARE FOUND")

                send(s,{
                    "id":1,
                    "method":"mining.submit",
                    "params":[
                        WALLET,
                        j["id"],
                        str(nonce)
                    ]
                })

# ================= MAIN =================
def start():
    while True:
        s = connect()

        send(s, {"id":1,"method":"mining.subscribe","params":[]})
        time.sleep(1)
        send(s, {"id":2,"method":"mining.authorize","params":[WALLET,"x"]})

        threading.Thread(target=listen,args=(s,),daemon=True).start()

        mine(s)

start()
