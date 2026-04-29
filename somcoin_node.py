# UPDATED 2026

from flask import Flask, request, jsonify, render_template
import requests
import hashlib
import time
import json
import os
import base64
import socket
import threading
import multiprocessing
import random

from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError

# =========================
# STRATUM SHARES STORAGE
# =========================
pool_shares = {}
pool_lock = threading.Lock()
submitted_hashes = set()

# =========================
# EARN SYSTEM (FIX)
# =========================
earn_lock = threading.Lock()

EARN_FILE = "earn.json"
balances = {}
referrals = {}
leaderboard = {}

# =========================
# APP INIT
# =========================
app = Flask(__name__)

MAX_DIFFICULTY = 6
MIN_DIFFICULTY = 2

# =========================
# DIFFICULTY SYSTEM
# =========================
def get_new_difficulty(chain):
    if len(chain) < 10:
        return 3

    last_block = chain[-1]
    prev_block = chain[-10]

    time_taken = last_block["timestamp"] - prev_block["timestamp"]
    expected_time = TARGET_BLOCK_TIME * 10

    difficulty = last_block.get("difficulty", 3)

    if time_taken < expected_time:
        difficulty += 1
    elif time_taken > expected_time:
        difficulty -= 1

    if difficulty > MAX_DIFFICULTY:
        difficulty = MAX_DIFFICULTY
    if difficulty < MIN_DIFFICULTY:
        difficulty = MIN_DIFFICULTY

    return difficulty

# =========================
# 🔥 SMART DIFFICULTY (BASED ON MINERS)
# =========================
def dynamic_difficulty():
    base = get_new_difficulty(blockchain)

    miner_count = len(p2p_peers)

    if miner_count < 5:
        return max(2, base - 1)

    elif miner_count < 20:
        return base

    elif miner_count < 100:
        return base + 1

    else:
        return base + 2

# ==================================================
# 🌍 P2P CONFIG (PRO GLOBAL - REAL BITCOIN STYLE 🚀)
# ==================================================

import time
import threading

# =========================
# 🔥 SCALE (SMART SYSTEM)
# =========================
MAX_PEERS = 1000
MAX_ACTIVE_PEERS = 64   # ⚠️ VERY IMPORTANT

p2p_peers = set()
peer_ips = set()
banned_ips = set()
peer_id_map = {}

# =========================
# 📊 PEER INTELLIGENCE
# =========================
peer_scores = {}
peer_failures = {}
peer_health = {}

# =========================
# 🧠 IP REPUTATION (ANTI-SYBIL)
# =========================
ip_reputation = {}

def update_ip_reputation(ip, success=True):
    score = ip_reputation.get(ip, 0)

    if success:
        score += 1
    else:
        score -= 2

    ip_reputation[ip] = score

    # 🚫 auto ban haddii aad u xun
    if score < -10:
        ban_ip(ip)

# =========================
# 🔒 NETWORK RULES
# =========================
ALLOWED_PORTS = {9334}

SEED_NODES = [
    "167.86.117.249:9334",
    "23.94.66.117:9334",
]

DNS_SEEDS = [
    "seed.somcoin.net",
    "seed1.somcoin.net",
    "seed2.somcoin.net",
]

# =========================
# 🔒 CONNECTION CONTROL
# =========================
MAX_CONNECTIONS_PER_IP = 5
MAX_FAILURES = 10
BAN_TIME = 300

# =========================
# ⚡ PERFORMANCE
# =========================
MAX_ACTIVE_BROADCAST = 8
MAX_DISCOVERY_PEERS = 20

# =========================
# 🧠 MEMORY
# =========================
MAX_PEER_IPS = 800

# =========================
# ⏱ HEALTH (FIXED 🔥)
# =========================
PEER_TIMEOUT = 180   # 3 min (REALISTIC)

# =========================
# 🔒 LOCK
# =========================
peers_lock = threading.Lock()

# ==================================================
# ✅ MARK ALIVE
# ==================================================
def mark_peer_alive(peer):
    peer_health[peer] = time.time()
    peer_failures[peer] = 0

# ==================================================
# ✅ REWARD
# ==================================================
def reward_peer(peer):
    ip = peer.split(":")[0]

    update_ip_reputation(ip, success=True)

    peer_scores[peer] = peer_scores.get(peer, 0) + 1

# ==================================================
# ❌ PUNISH (SMART)
# ==================================================
def punish_peer(peer):

    if peer in SEED_NODES:
        return

    ip = peer.split(":")[0]

    update_ip_reputation(ip, success=False)

    peer_failures[peer] = peer_failures.get(peer, 0) + 1
    peer_scores[peer] = peer_scores.get(peer, 0) - 1

    if peer_failures[peer] >= MAX_FAILURES:
        ban_ip(ip)

    if (
        peer_failures[peer] >= MAX_FAILURES or
        peer_scores.get(peer, 0) < -10
    ):
        print("🚫 Removing bad peer:", peer)

        with peers_lock:
            p2p_peers.discard(peer)

        peer_health.pop(peer, None)
        peer_failures.pop(peer, None)
        peer_scores.pop(peer, None)

# ==================================================
# 🧠 BEST PEERS (ACTIVE SET)
# ==================================================
def get_best_peers(limit=MAX_ACTIVE_PEERS):

    def score(p):
        ip = p.split(":")[0]

        return (
            peer_scores.get(p, 0) * 2 +
            ip_reputation.get(ip, 0) +
            (time.time() - peer_health.get(p, 0)) * -0.1
        )

    sorted_peers = sorted(
        p2p_peers,
        key=score,
        reverse=True
    )

    return sorted_peers[:limit]

# ==================================================
# 🧹 CLEAN DEAD PEERS
# ==================================================
def clean_dead_peers():
    while True:
        try:
            now = time.time()

            for peer in list(peer_health.keys()):

                last_seen = peer_health.get(peer, 0)
                fails = peer_failures.get(peer, 0)

                if now - last_seen > PEER_TIMEOUT:

                    peer_failures[peer] = fails + 1

                    print(f"⚠️ Inactive: {peer} | fails={peer_failures[peer]}")

                    # ❗ remove ONLY after multiple fails
                    if peer_failures[peer] >= MAX_FAILURES:

                        print("🚫 Removing dead peer:", peer)

                        with peers_lock:
                            p2p_peers.discard(peer)

                        peer_health.pop(peer, None)
                        peer_failures.pop(peer, None)
                        peer_scores.pop(peer, None)

        except Exception as e:
            print("Clean error:", e)

        time.sleep(30)

# ==================================================
# 🔄 PEER ROTATION (KEEP BEST PEERS ONLY)
# ==================================================
def rotate_peers():
    while True:
        try:
            with peers_lock:  # 🔒 muhiim (thread-safe)

                if len(p2p_peers) > MAX_ACTIVE_PEERS:

                    weakest = sorted(
                        p2p_peers,
                        key=lambda p: peer_scores.get(p, 0)
                    )[:10]

                    for p in weakest:
                        print("🔄 Removing weak peer:", p)
                        p2p_peers.discard(p)

                        peer_scores.pop(p, None)
                        peer_failures.pop(p, None)
                        peer_health.pop(p, None)

        except Exception as e:
            print("Rotate error:", e)

        time.sleep(20)

# ==================================================
# 🚫 BAN SYSTEM
# ==================================================
banned_until = {}

def is_banned(ip):
    if ip in banned_until:
        if time.time() < banned_until[ip]:
            return True
        else:
            banned_until.pop(ip, None)
    return False

def ban_ip(ip):
    banned_until[ip] = time.time() + BAN_TIME
    banned_ips.add(ip)
    print("⛔ Banned IP:", ip)

def smart_ban(ip, reason="unknown"):
    print(f"🚫 Banning {ip} | reason={reason}")

    penalty = ip_reputation.get(ip, 0)
    ban_time = BAN_TIME * (1 + abs(penalty) // 5)

    banned_until[ip] = time.time() + ban_time
    banned_ips.add(ip)

# ==================================================
# 🌐 SAFE ADD PEER (STRICT)
# ==================================================

def add_peer_safe(ip, port):

    try:
        # =========================
        # 🔒 BASIC VALIDATION
        # =========================
        if not ip or not isinstance(ip, str):
            return False

        ip = ip.strip()

        try:
            port = int(port)
        except:
            return False

        if port not in ALLOWED_PORTS:
            return False

        # =========================
        # 🚫 BLOCK INVALID IPS
        # =========================
        if (
            ip.startswith("127.") or
            ip.startswith("0.") or
            ip.startswith("255.") or
            ip == "0.0.0.0"
        ):
            return False

        # =========================
        # 🚫 BAN CHECK
        # =========================
        if is_banned(ip):
            return False

        # =========================
        # 🔥 CONNECTION LIMIT PER IP (IMPORTANT)
        # =========================
        same_ip = [p for p in p2p_peers if p.startswith(ip + ":")]
        if len(same_ip) >= MAX_CONNECTIONS_PER_IP:
            return False

        # =========================
        # 🔒 BUILD PEER
        # =========================
        peer = f"{ip}:{port}"

        # =========================
        # 🚫 DUPLICATE CHECK
        # =========================
        if peer in p2p_peers:
            return False

        # =========================
        # 🔒 GLOBAL LIMIT
        # =========================
        if len(p2p_peers) >= MAX_PEERS:
            return False

        # =========================
        # 🔒 THREAD SAFE ADD
        # =========================
        with peers_lock:

            # double-check inside lock (important)
            if peer in p2p_peers:
                return False

            p2p_peers.add(peer)

            save_peers_safe()

            # 🧠 MEMORY PROTECTION
            if len(peer_ips) < MAX_PEER_IPS:
                peer_ips.add(ip)

            # 📊 INIT STATS
            peer_scores[peer] = 0
            peer_failures[peer] = 0
            peer_health[peer] = time.time()

        print("🌐 Peer added:", peer)
        return True

    except Exception as e:
        print("Add peer error:", e)
        return False

# =========================
# 🔥 SMART DISCOVERY (FINAL FIXED )
# =========================
def smart_discovery():
    while True:
        try:
            all_peers = list(p2p_peers)

            if not all_peers:
                time.sleep(5)
                continue

            # =========================
            # 🔥 BEST + RANDOM (IMPORTANT)
            # =========================
            best_peers = sorted(
                all_peers,
                key=lambda p: peer_scores.get(p, 0),
                reverse=True
            )[:10]

            random_peers = random.sample(
                all_peers,
                min(10, len(all_peers))
            )

            selected_peers = list(set(best_peers + random_peers))

            # =========================
            # 🔁 LOOP
            # =========================
            for peer in selected_peers:

                if peer == f"{NODE_IP}:{P2P_PORT}":
                    continue

                try:
                    ip, port = peer.split(":")
                    port = int(port)

                    # 🚫 banned
                    if is_banned(ip):
                        continue

                    r = requests.get(
                        f"http://{ip}:{port}/peers",
                        timeout=2
                    )

                    if r.status_code != 200:
                        punish_peer(peer)
                        continue

                    reward_peer(peer)
                    mark_peer_alive(peer)

                    data = r.json()
                    new_peers = data.get("peers", [])

                    # =========================
                    # 🔥 ADD NEW PEERS (SAFE)
                    # =========================
                    for new_peer in new_peers:

                        try:
                            nip, nport = new_peer.split(":")
                            nport = int(nport)

                            # 🔒 use safe add (IMPORTANT)
                            add_peer_safe(nip, nport)

                        except Exception:
                            continue

                except Exception:
                    punish_peer(peer)

            # =========================
            # 🧹 CLEAN BAD PEERS (LIGHT)
            # =========================
            for peer in list(p2p_peers):
                if peer_scores.get(peer, 0) < -5:
                    p2p_peers.discard(peer)
                    peer_scores.pop(peer, None)
                    peer_failures.pop(peer, None)
                    peer_health.pop(peer, None)

        except Exception as e:
            print("Discovery error:", e)

        time.sleep(6)

def gossip_peers():
    while True:
        for peer in list(p2p_peers):
            try:
                ip, port = peer.split(":")
                requests.post(f"http://{ip}:{port}/peers", json={
                    "peers": list(p2p_peers)[:20]
                }, timeout=2)
            except:
                pass

        time.sleep(10)

def resolve_dns_seeds():
    new_peers = []

    for seed in DNS_SEEDS:
        try:
            ips = socket.gethostbyname_ex(seed)[2]
            for ip in ips:
                peer = f"{ip}:{P2P_PORT}"
                new_peers.append(peer)
        except Exception as e:
            print("DNS seed error:", seed, e)

    return new_peers


def dns_bootstrap():
    while True:
        try:
            peers = resolve_dns_seeds()

            for p in peers:
                try:
                    ip, port = p.split(":")
                    add_peer_safe(ip, int(port))
                except:
                    continue

        except Exception as e:
            print("DNS bootstrap error:", e)

        time.sleep(60)

def bootstrap_peers():
    hardcoded = [
        "node1.somcoin.net:9334",
        "node2.somcoin.net:9334"
    ]

    for p in hardcoded:
        try:
            ip, port = p.split(":")
            add_peer_safe(ip, int(port))
        except:
            continue

def ensure_minimum_peers():
    MIN_PEERS = 15   # 🔥 stronger network

    while True:
        try:
            with peers_lock:
                current = len(p2p_peers)

            if current < MIN_PEERS:
                print(f"⚠️ Low peers ({current}) → recovering network...")

                # 🔁 RECONNECT SEEDS
                for seed in SEED_NODES:
                    try:
                        ip, port = seed.split(":")
                        port = int(port)

                        if (
                            ip.startswith("0.") or
                            ip.startswith("127.") or
                            ip.startswith("255.") or
                            ip == "0.0.0.0"
                        ):
                            continue

                        s = socket.socket()
                        s.settimeout(3)
                        s.connect((ip, port))

                        s.sendall((json.dumps({
                            "type": "hello",
                            "port": P2P_PORT,
                            "node_id": NODE_ID,
                            "public_key": NODE_PUBLIC_KEY,
                            "signature": sign_message(NODE_ID)
                        }) + "\n").encode())

                        s.close()

                        with peers_lock:
                            if len(p2p_peers) < MAX_PEERS:
                                p2p_peers.add(seed)

                                if len(peer_ips) < MAX_PEER_IPS:
                                    peer_ips.add(ip)

                                peer_scores[seed] = 5
                                mark_peer_alive(seed)

                        print("🔁 Reconnected seed:", seed)

                    except:
                        continue

                # 🌐 EXTRA BOOST
                random_bootstrap()
                request_peers()

        except Exception as e:
            print("Ensure peer error:", e)

        time.sleep(8)


def safe_save_blockchain():
    try:
        tmp_file = "blockchain.json.tmp"
        final_file = "blockchain.json"

        # ensure dir
        open(tmp_file, "w").close()

        with open(tmp_file, "w") as f:
            json.dump(blockchain, f)

        os.replace(tmp_file, final_file)

    except Exception as e:
        print("Save error:", e)

# ==================================================
# 🌍 AUTO SEED EXPANSION (GLOBAL NETWORK GROWTH)
# ==================================================

def expand_seed_nodes():
    global SEED_NODES

    try:
        for peer in list(p2p_peers):

            # 🚫 skip duplicates
            if peer in SEED_NODES:
                continue

            ip = peer.split(":")[0]

            # 🚫 skip banned
            if ip in banned_ips:
                continue

            # ✅ add new seed
            SEED_NODES.append(peer)

        # 🔒 limit seeds (important)
        SEED_NODES = list(set(SEED_NODES))[:50]

        print("🌍 Seeds expanded:", len(SEED_NODES))

    except Exception as e:
        print("Seed expand error:", e)


# ==================================================
# 🔁 AUTO SEED EXPAND LOOP
# ==================================================

def auto_seed_expand():
    while True:
        try:
            expand_seed_nodes()

        except Exception as e:
            print("Auto seed error:", e)

        time.sleep(30)

# ==================================================
# 🌐 AUTO SEED CONTROL (SMART DECENTRALIZATION)
# ==================================================
def auto_seed_control():

    global SEED_NODES

    ORIGINAL_SEEDS = [
        "167.86.117.249:9334",
        "23.94.66.117:9334",
    ]

    SEED_ACTIVE = True

    while True:
        try:
            peer_count = len(p2p_peers)

            if peer_count >= 50 and SEED_ACTIVE:
                print(f"🔥 Strong network ({peer_count} peers) → DISABLING seeds")
                SEED_NODES = []
                SEED_ACTIVE = False

            elif peer_count < 20 and not SEED_ACTIVE:
                print(f"⚠️ Weak network ({peer_count} peers) → ENABLING seeds")
                SEED_NODES = ORIGINAL_SEEDS.copy()
                SEED_ACTIVE = True

        except Exception as e:
            print("Seed control error:", e)

        time.sleep(15)

# ==================================================
# API: GET PEERS
# ==================================================
@app.route("/add_peer/<peer>")
def add_peer(peer):
    try:
        ip, port = peer.split(":")
        port = int(port)

        if port not in ALLOWED_PORTS:
            return {"error": "invalid port"}

        clean_peer = f"{ip}:{port}"

        if clean_peer not in p2p_peers:
            p2p_peers.add(clean_peer)
            peer_scores[clean_peer] = 0
            save_peers_safe()

        return {
            "status": "peer added",
            "peer": clean_peer,
            "total": len(p2p_peers)
        }

    except Exception as e:
        return {"error": str(e)}

# ==================================================
# NETWORK INFO
# ==================================================
NETWORK_NAME = "SomCoin"
CREATOR = "Zakariya Adan"
NETWORK_ID = "SOM_MAINNET_1"
CREATED_YEAR = "2026"

BLOCKCHAIN_FILE = "blockchain.json"
MEMPOOL_FILE = "mempool.json"
PEERS_FILE = "peers.json"

blockchain = []
pending_transactions = []


# ==================================================
# UTXO SET
# ==================================================

utxo_set = {}

blockchain_lock = threading.Lock()

# ==================================================
# STORAGE (ULTRA SAFE
# ==================================================
save_lock = threading.Lock()

def save_data():
    global blockchain

    try:
        with save_lock:  # 🔒 prevent concurrent writes

            tmp_file = BLOCKCHAIN_FILE + ".tmp"

            # write temp file
            with open(tmp_file, "w") as f:
                json.dump(blockchain, f)

                # 🔥 force write to disk (important!)
                f.flush()
                os.fsync(f.fileno())

            # 🔥 atomic replace (safe even if crash)
            os.replace(tmp_file, BLOCKCHAIN_FILE)

    except Exception as e:
        print("❌ Blockchain save error:", e)

    # =========================================
    # SAVE EARN SYSTEM 🔥
    # =========================================
    try:
        with earn_lock:

            data = {
                "balances": balances,
                "referrals": referrals,
                "leaderboard": leaderboard
            }

            tmp = EARN_FILE + ".tmp"

            with open(tmp, "w") as f:
                json.dump(data, f)

            os.replace(tmp, EARN_FILE)

    except Exception as e:
        print("Earn save error:", e)

# ==================================================
# 💾 SAVE PEERS (ULTRA SAFE 🔥)
# ==================================================
def save_peers():
    try:
        tmp = PEERS_FILE + ".tmp"

        with open(tmp, "w") as f:
            json.dump(list(p2p_peers), f)

        os.replace(tmp, PEERS_FILE)

    except Exception as e:
        print("❌ Save peers error:", e)

# =========================
# 🔥 PEER SAVE RATE LIMIT
# =========================
last_peer_save = 0

def save_peers_safe():
    global last_peer_save

    if time.time() - last_peer_save < 5:
        return

    save_peers()
    last_peer_save = time.time()

# ==================================================
# LOAD DATA (ULTRA PRO + DECENTRALIZED 🔥)
# ==================================================
def load_data():

    global blockchain, pending_transactions, p2p_peers
    global balances, referrals, leaderboard

    blockchain = []
    pending_transactions = []
    p2p_peers = set()

    # ==============================
    # LOAD BLOCKCHAIN
    # ==============================
    if os.path.exists(BLOCKCHAIN_FILE):
        try:
            with open(BLOCKCHAIN_FILE, "r") as f:
                data = json.load(f)

            if isinstance(data, list) and len(data) > 0:
                blockchain = data
                print("📦 Blockchain loaded:", len(blockchain), "blocks")
            else:
                print("⚠️ Blockchain empty")

        except Exception as e:
            print("❌ Blockchain load error:", e)

            # 🔧 AUTO RECOVERY
            try:
                with open(BLOCKCHAIN_FILE, "r") as f:
                    raw = f.read()

                cut = raw.rfind('},{"index":')

                if cut != -1:
                    fixed = raw[:cut] + "]"
                    data = json.loads(fixed)

                    if isinstance(data, list) and len(data) > 0:
                        blockchain = data
                        print("🛠 Recovered blocks:", len(blockchain))

            except Exception as e2:
                print("❌ Recovery failed:", e2)

    # ==============================
    # LOAD MEMPOOL
    # ==============================
    if os.path.exists(MEMPOOL_FILE):
        try:
            with open(MEMPOOL_FILE) as f:
                raw = f.read().strip()

                if raw:
                    pending_transactions = json.loads(raw)
                else:
                    pending_transactions = []

            print("📥 Mempool loaded:", len(pending_transactions))

        except Exception as e:
            print("❌ Mempool load error:", e)
            pending_transactions = []

    # ==============================
    # LOAD PEERS (SMART CLEAN 🔥)
    # ==============================
    if os.path.exists(PEERS_FILE):
        try:
            with open(PEERS_FILE) as f:
                raw = f.read().strip()

                if raw:
                    loaded = json.loads(raw)

                    cleaned = set()

                    for p in loaded:
                        try:
                            if not isinstance(p, str):
                                continue

                            if ":" not in p:
                                continue

                            ip, port = p.split(":")
                            port = int(port)

                            # 🔒 FILTER INVALID
                            if (
                                ip.startswith("127.") or
                                ip.startswith("0.") or
                                ip.startswith("255.") or
                                ip == "0.0.0.0"
                            ):
                                continue

                            if port not in ALLOWED_PORTS:
                                continue

                            cleaned.add(f"{ip}:{port}")

                        except:
                            continue

                    p2p_peers = cleaned

                else:
                    p2p_peers = set()

        except Exception as e:
            print("❌ Peers load error:", e)
            p2p_peers = set()

    print("🌐 Peers loaded:", len(p2p_peers))

    # 🔥 SAVE AFTER CLEAN (VERY IMPORTANT)
    save_peers_safe()

    # ==============================
    # LOAD EARN SYSTEM
    # ==============================
    if os.path.exists(EARN_FILE):
        try:
            with open(EARN_FILE) as f:
                data = json.load(f)

            balances = data.get("balances", {})
            referrals = data.get("referrals", {})
            leaderboard = data.get("leaderboard", {})

            print("💰 Earn system loaded")

        except Exception as e:
            print("❌ Earn load error:", e)

# ==================================================
# ECONOMICS
# ==================================================
TARGET_BLOCK_TIME = 60
difficulty = 4
TX_FEE = 0.01
MAX_TX_PER_BLOCK = 50
MAX_MEMPOOL = 1000

TARGET_BLOCK_TIME = 60
initial_reward = 10
halving_interval = 210000
MIN_REWARD = 1
max_supply = 21000000

P2P_PORT = int(os.getenv("P2P_PORT", 9334))
HTTP_PORT = int(os.getenv("PORT", 9443))

# ==================================================
# DIFFICULTY ADJUSTMENT
# ==================================================

DIFFICULTY_ADJUSTMENT_INTERVAL = 10

def adjust_difficulty():

    global difficulty

    # haddii blocks yar yihiin ha bedelin difficulty
    if len(blockchain) < DIFFICULTY_ADJUSTMENT_INTERVAL:
        return

    last_block = blockchain[-1]
    prev_block = blockchain[-DIFFICULTY_ADJUSTMENT_INTERVAL]

    actual_time = last_block["timestamp"] - prev_block["timestamp"]
    expected_time = TARGET_BLOCK_TIME * DIFFICULTY_ADJUSTMENT_INTERVAL

    # haddii blocks degdeg ku yimaadaan → difficulty kordhi
    if actual_time < expected_time / 2:

        difficulty += 1

        if difficulty > MAX_DIFFICULTY:
            difficulty = MAX_DIFFICULTY

        print("Difficulty increased:", difficulty)

    # haddii blocks gaabis noqdaan → difficulty dhimi
    elif actual_time > expected_time * 2:

        if difficulty > 1:
            difficulty -= 1

        print("Difficulty decreased:", difficulty)
# ==================================================
# HASH
# ==================================================
def calculate_hash(index, prev_hash, timestamp, nonce, tx_str):
    data = f"{index}{prev_hash}{timestamp}{nonce}{tx_str}"
    return pow_hash(data)

def sha(data):
    return hashlib.sha256(
        hashlib.sha256(data.encode()).digest()
    ).hexdigest()

# =========================
# 🔥 POW HASH (SCRYPT)
# =========================
def pow_hash(data):
    import hashlib
    return hashlib.scrypt(
        data.encode(),
        salt=b"somcoin",
        n=1024,
        r=1,
        p=1
    ).hex()

# ==================================================
# BUILD BLOCK HEADER
# ==================================================
def build_header(index, prev_hash, timestamp, tx_str):
    header = f"{index}{prev_hash}{timestamp}{tx_str}"
    return header.encode()
# ==================================================
# MINER WORKER
# ==================================================
def mine_worker(start, step, index, prev_hash, txs, difficulty):

    nonce = start

    # timestamp hal mar
    timestamp = time.time()

    # json hal mar
    tx_str = json.dumps(txs, sort_keys=True)

    while True:

        h = calculate_hash(
            index,
            prev_hash,
            timestamp,
            nonce,
            tx_str
        )

        if h.startswith("0" * difficulty):
            return nonce, timestamp, h

        nonce += step


# ==================================================
# MULTI CPU MINER
# ==================================================
def mine_block(index, prev_hash, block_txs, difficulty):

    cpu = multiprocessing.cpu_count()

    with multiprocessing.Pool(cpu) as pool:

        jobs = []

        for i in range(cpu):

            job = pool.apply_async(
                mine_worker,
                (i, cpu, index, prev_hash, block_txs, difficulty)
            )

            jobs.append(job)

        while True:

            for job in jobs:

                if job.ready():

                    nonce, ts, h = job.get()

                    pool.terminate()
                    pool.join()

                    return nonce, ts, h

            time.sleep(0.01)


# ==================================================
# GENESIS (LOCKED)
# ==================================================
def create_genesis():

    global blockchain

    # haddii blockchain file hore u jiro → ha samayn genesis
    if os.path.exists(BLOCKCHAIN_FILE):
        try:
            with open(BLOCKCHAIN_FILE) as f:
                data = json.load(f)

            if isinstance(data, list) and len(data) > 0:
                blockchain = data
                print("Existing blockchain detected — genesis skipped")
                return

        except:
            pass

    # haddii chain ma jiro → samee genesis
    genesis = {
        "index": 0,
        "timestamp": 1700000000,
        "transactions": [],
        "nonce": 0,
        "previous_hash": "0",
        "difficulty": difficulty
    }

    # HASH GENESIS
    genesis["hash"] = calculate_hash(
        genesis["index"],
        genesis["previous_hash"],
        genesis["timestamp"],
        genesis["nonce"],
        genesis["transactions"]
    )

    blockchain.append(genesis)

    save_data()

    print("Genesis block created")
# ==================================================
# REBUILD UTXO SET
# ==================================================
def rebuild_utxo():

    global utxo_set

    utxo_set = {}

    for block in blockchain:

        for tx in block["transactions"]:

            txid = hashlib.sha256(
                json.dumps(tx, sort_keys=True).encode()
            ).hexdigest()

            for inp in tx.get("inputs", []):
                key = f'{inp["txid"]}:{inp["index"]}'
                if key in utxo_set:
                    del utxo_set[key]

            for i, out in enumerate(tx.get("outputs", [])):

                key = f"{txid}:{i}"

                utxo_set[key] = {
                    "address": out["address"],
                    "amount": out["amount"]
                }

# =========================
# TX HASH
# =========================
def tx_hash(tx):
    data = json.dumps(tx, sort_keys=True).encode()
    return hashlib.sha256(hashlib.sha256(data).digest()).hexdigest()


# ==================================================
# UPDATE UTXO (FINAL PRO)
# ==================================================
def update_utxo(block):

    global utxo_set

    for tx in block["transactions"]:

        # 🔒 SKIP INVALID TX
        if not verify_tx(tx):
            print("❌ Skipping invalid tx in UTXO")
            continue

        txid = tx_hash(tx)

        # =========================
        # REMOVE INPUTS (SPENT)
        # =========================
        if tx.get("sender") != "NETWORK":

            for inp in tx.get("inputs", []):
                key = f'{inp["txid"]}:{inp["index"]}'

                if key in utxo_set:
                    del utxo_set[key]

        # =========================
        # ADD OUTPUTS (NEW UTXO)
        # =========================
        for index, out in enumerate(tx.get("outputs", [])):

            # 🔒 CHECK AMOUNT
            if out.get("amount", 0) <= 0:
                continue

            utxo_set[f"{txid}:{index}"] = {
                "address": out.get("address"),
                "amount": round(out.get("amount"), 8)
            }


# ==================================================
# SAFE UPDATE (ANTI-CRASH)
# ==================================================
def safe_update_utxo(block):

    try:
        update_utxo(block)

    except Exception as e:
        print("⚠️ UTXO error → rebuilding:", e)
        rebuild_utxo()


# ==================================================
# SIGN TRANSACTION
# ==================================================
import hashlib
from ecdsa import SigningKey, SECP256k1

def sign_transaction(tx, private_key_hex):

    # remove signature haddii uu jiro
    tx_copy = dict(tx)
    tx_copy.pop("signature", None)

    message = json.dumps(tx_copy, sort_keys=True).encode()
    h = hashlib.sha256(message).digest()

    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    signature = sk.sign(h).hex()

    return signature

# ==================================================
# VERIFY SIGNATURE (FIXED + SECURE 🔥)
# ==================================================
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
import hashlib
import json

def verify_transaction(tx):
    try:
        signature_hex = tx.get("signature")
        public_key_hex = tx.get("public_key")

        if not signature_hex or not public_key_hex:
            return False

        try:
            signature = bytes.fromhex(signature_hex)
            public_key = bytes.fromhex(public_key_hex)
        except:
            return False

        if len(public_key) not in (64, 65):
            return False

        tx_copy = dict(tx)
        tx_copy.pop("signature", None)

        message = json.dumps(tx_copy, sort_keys=True).encode()
        h = hashlib.sha256(message).digest()

        vk = VerifyingKey.from_string(public_key, curve=SECP256k1)

        return vk.verify(signature, h)

    except BadSignatureError:
        return False
    except Exception as e:
        print("Verify error:", e)
        return False

# ==================================================
# VERIFY NODE (ANTI-FAKE)
# ==================================================
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
import hashlib

def verify_node(node_id, public_key, signature):
    try:
        if not node_id or not public_key or not signature:
            return False

        if len(node_id) != 64:
            return False

        pk_bytes = bytes.fromhex(public_key)

        if len(pk_bytes) not in (64, 65):
            return False

        vk = VerifyingKey.from_string(pk_bytes, curve=SECP256k1)

        h = hashlib.sha256(node_id.encode()).digest()

        return vk.verify(bytes.fromhex(signature), h)

    except BadSignatureError:
        return False
    except Exception as e:
        print("Node verify error:", e)
        return False


# ==================================================
# CHECK DOUBLE SPEND (MEMPOOL)
# ==================================================
def is_utxo_spent_in_mempool(txid, index):

    for tx in pending_transactions:
        for inp in tx.get("inputs", []):
            if inp["txid"] == txid and inp["index"] == index:
                return True

    return False
# ==================================================
# AUTO CLEAN MEMPOOL (ANTI-SPAM 🔥)
# ==================================================
def clean_mempool():
    global pending_transactions

    cleaned = []
    used_inputs = set()
    now = time.time()

    for tx in pending_transactions:
        try:
            # ❌ remove invalid tx
            if not verify_tx(tx):
                continue

            # ❌ remove old tx (10 min)
            if now - tx.get("timestamp", now) > 600:
                continue

            # ❌ prevent double spend gudaha mempool
            valid = True
            for inp in tx.get("inputs", []):
                key = f'{inp["txid"]}:{inp["index"]}'

                if key in used_inputs:
                    valid = False
                    break

                used_inputs.add(key)

            if not valid:
                continue

            cleaned.append(tx)

        except:
            continue

    # 🔥 LIMIT SIZE (ANTI-SPAM)
    cleaned = sorted(cleaned, key=lambda x: x.get("fee", 0), reverse=True)
    pending_transactions = cleaned[:MAX_MEMPOOL]


# ==================================================
# CREATE TRANSACTION (UTXO) FINAL (FIXED)
# ==================================================
def create_transaction(sender, receiver, amount, fee=0.001):

    # 🔒 VALIDATE INPUT
    if not sender or not receiver:
        return None, "Invalid address"

    try:
        amount = float(amount)
    except:
        return None, "Invalid amount format"

    if amount <= 0:
        return None, "Amount must be > 0"

    # 🔒 CHECK BALANCE (pending included)
    if balance_with_pending(sender) < amount + fee:
        return None, "Insufficient (including pending)"

    inputs = []
    total = 0

    # 🔥 SORT UTXOs (small → big, better selection)
    user_utxos = []

    for key, utxo in utxo_set.items():
        if utxo["address"] == sender:
            user_utxos.append((key, utxo))

    user_utxos.sort(key=lambda x: x[1]["amount"])

    # =========================
    # SELECT INPUTS
    # =========================
    for key, utxo in user_utxos:

        txid, index = key.split(":")
        index = int(index)

        # 🚫 SKIP haddii mempool ku jiro
        if is_utxo_spent_in_mempool(txid, index):
            continue

        inputs.append({
            "txid": txid,
            "index": index
        })

        total += utxo["amount"]

        if total >= amount + fee:
            break

    # ❌ haddii lacag ku filan la waayo
    if total < amount + fee:
        return None, "Insufficient balance"

    # =========================
    # OUTPUTS
    # =========================
    outputs = []

    # lacagta la dirayo
    outputs.append({
        "address": receiver,
        "amount": round(amount, 8)
    })

    # change (haddii wax ka haro)
    change = round(total - amount - fee, 8)

    if change > 0.00000001:
        outputs.append({
            "address": sender,
            "amount": change
        })

    # =========================
    # FINAL TX
    # =========================
    tx = {
        "sender": sender,
        "inputs": inputs,
        "outputs": outputs,
        "fee": round(fee, 8),
        "timestamp": time.time(),
        "public_key": "",
        "signature": ""
    }

    return tx, "OK"


# ==================================================
# BALANCE (UTXO BASED)
# ==================================================
def balance(addr):

    bal = 0

    for utxo in utxo_set.values():
        if utxo["address"] == addr:
            bal += utxo["amount"]

    return round(bal, 8)


# ==================================================
# BALANCE WITH PENDING (MEMPOOL AWARE)
# ==================================================
def balance_with_pending(addr):

    bal = balance(addr)

    for tx in pending_transactions:

        # haddii sender yahay → subtract
        for inp in tx.get("inputs", []):
            key = f'{inp["txid"]}:{inp["index"]}'
            utxo = utxo_set.get(key)

            if utxo and utxo["address"] == addr:
                bal -= utxo["amount"]

        # haddii receiver yahay → add
        for out in tx.get("outputs", []):
            if out["address"] == addr:
                bal += out["amount"]

    return round(bal, 8)


# ==================================================
# NEW WALLET
# ==================================================
@app.route("/wallet/new")
def new_wallet():
    from ecdsa import SigningKey, SECP256k1
    import hashlib

    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()

    private_key = sk.to_string().hex()
    public_key = vk.to_string().hex()

    address = "SOM" + hashlib.sha256(public_key.encode()).hexdigest()[:40]

    return jsonify({
        "private_key": private_key,
        "public_key": public_key,
        "address": address
    })

@app.route("/explorer")
def explorer():
    return jsonify({
        "blocks": len(blockchain),
        "latest_block": blockchain[-1] if blockchain else None,
        "txs": len(pending_transactions)
    })

faucet_cache = {}


# =========================
# GET UTXOS
# =========================
@app.route("/utxos/<address>")
def get_utxos(address):
    result = []

    for key, utxo in utxo_set.items():
        if utxo["address"] == address:
            txid, index = key.split(":")
            result.append({
                "txid": txid,
                "index": int(index),
                "amount": utxo["amount"]
            })

    return jsonify({"utxos": result})

# ==================================================
# SEND TRANSACTION (FINAL PRO 🔥)
# ==================================================
MIN_TX_FEE = 0.01

@app.route("/send", methods=["POST"])
def send():

    data = request.json

    if not data:
        return jsonify({"error": "no data"}), 400

    sender = data.get("from")
    receiver = data.get("to")

    # =========================
    # AMOUNT VALIDATION
    # =========================
    try:
        amount = float(data.get("amount", 0))
    except:
        return jsonify({"error": "invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "invalid amount"}), 400

    # =========================
    # FEE SYSTEM
    # =========================
    try:
        fee = float(data.get("fee", get_recommended_fee()))
    except:
        fee = get_recommended_fee()

    if fee < MIN_TX_FEE:
        return jsonify({
            "error": "fee too low",
            "minimum_fee": MIN_TX_FEE
        }), 400

    # =========================
    # REQUIRED FIELDS
    # =========================
    signature = data.get("signature")
    public_key = data.get("public_key")

    if not sender or not receiver or not signature or not public_key:
        return jsonify({"error": "missing fields"}), 400

    # =========================
    # CREATE TX
    # =========================
    tx, status = create_transaction(sender, receiver, amount, fee)

    if not tx:
        return jsonify({"error": status}), 400

    tx["public_key"] = public_key
    tx["signature"] = signature

    # =========================
    # VERIFY FULL TX 🔥
    # =========================
    if not verify_tx(tx):
        return jsonify({"error": "Invalid transaction"}), 400

    # =========================
    # MEMPOOL SAFE ADD 🔥
    # =========================
    with mempool_lock:

        if len(pending_transactions) >= MAX_MEMPOOL:
            return jsonify({"error": "mempool full"}), 400

        txid = tx_hash(tx)

        # ❌ duplicate protection
        if any(tx_hash(t) == txid for t in pending_transactions):
            return jsonify({"error": "duplicate transaction"}), 400

        pending_transactions.append(tx)

    return jsonify({
        "status": "transaction added",
        "txid": txid,
        "fee": fee,
        "recommended_fee": get_recommended_fee(),
        "mempool_size": len(pending_transactions)
    })

# ==================================================
# TOTAL SUPPLY
# ==================================================
def total_supply():

    total = 0.0

    for block in blockchain:

        for tx in block.get("transactions", []):

            # only count minted coins
            if tx.get("sender") == "NETWORK":

                for out in tx.get("outputs", []):

                    amount = out.get("amount", 0)

                    # 🔒 skip invalid values
                    if amount <= 0:
                        continue

                    total += float(amount)

    return round(total, 8)

# ==================================================
# ⚡ HASHRATE CALCULATION (ADD THIS 🔥)
# ==================================================
def calculate_hashrate():
    if len(blockchain) < 10:
        return 0

    last = blockchain[-1]
    prev = blockchain[-10]

    time_taken = last["timestamp"] - prev["timestamp"]

    if time_taken == 0:
        return 0

    return round((10 / time_taken) * (2 ** last.get("difficulty", 1)), 2)

def get_recommended_fee():
    if len(pending_transactions) < 10:
        return 0.001
    elif len(pending_transactions) < 50:
        return 0.005
    else:
        return 0.01

# ==================================================
# BLOCK REWARD (HALVING + MAX SUPPLY)
# ==================================================
def block_reward():

    # halving calculation
    halv = len(blockchain) // halving_interval
    reward = initial_reward / (2 ** halv)

    if reward < MIN_REWARD:
        reward = MIN_REWARD

    current_supply = total_supply()
    remaining = max_supply - current_supply

    # if max supply reached
    if remaining <= 0:
        return 0

    # do not exceed supply cap
    if reward > remaining:
        reward = remaining

    return reward


# ==================================================
# VERIFY TX (UTXO + SIGNATURE) - FINAL FIXED
# ==================================================
def verify_tx(tx, used_inputs=None):

    try:

        # track used inputs (prevent double spend gudaha block)
        if used_inputs is None:
            used_inputs = set()

        # =========================
        # COINBASE (REWARD)
        # =========================
        if tx.get("sender") == "NETWORK":
            if tx.get("inputs"):
                return False
            return True

        # =========================
        # BASIC CHECK
        # =========================
        if "inputs" not in tx or "outputs" not in tx:
            return False

        if not tx["inputs"] or not tx["outputs"]:
            return False

        if "public_key" not in tx or "signature" not in tx:
            return False

        if "sender" not in tx:
            return False

        # =========================
        # SIGNATURE VERIFY (HEX FIX)
        # =========================
        try:
            public_key_hex = tx.get("public_key")
            signature_hex = tx.get("signature")

            # remove signature before hashing
            tx_copy = dict(tx)
            tx_copy.pop("signature", None)

            message = json.dumps(tx_copy, sort_keys=True).encode()
            h = hashlib.sha256(message).digest()

            vk = VerifyingKey.from_string(
                bytes.fromhex(public_key_hex),
                curve=SECP256k1
            )

            if not vk.verify(bytes.fromhex(signature_hex), h):
                return False

        except Exception as e:
            print("Verify error:", e)
            return False

        # =========================
        # UTXO CHECK
        # =========================
        input_sum = 0
        output_sum = 0

        for inp in tx["inputs"]:

            if "txid" not in inp or "index" not in inp:
                return False

            key = f'{inp["txid"]}:{inp["index"]}'

            # 🚫 DOUBLE SPEND gudaha block
            if key in used_inputs:
                return False

            utxo = utxo_set.get(key)

            if not utxo:
                return False

            # check owner
            if utxo["address"] != tx["sender"]:
                return False

            input_sum += utxo["amount"]
            used_inputs.add(key)

        # =========================
        # OUTPUT CHECK
        # =========================
        for out in tx["outputs"]:

            if "address" not in out or "amount" not in out:
                return False

            if out["amount"] <= 0:
                return False

            output_sum += out["amount"]

        # =========================
        # PREVENT OVERSPEND
        # =========================
        if output_sum > input_sum:
            return False

        # fee
        tx["fee"] = round(input_sum - output_sum, 8)

        return True

    except Exception as e:
        print("TX verify fatal error:", e)
        return False


# ==================================================
# BLOCK VALIDATION
# ==================================================
def validate_block(b, chain_ref):

    if b["index"] != len(chain_ref):
        return False

    if b["previous_hash"] != chain_ref[-1]["hash"]:
        return False

    # same tx encoding as miner
    tx_str = json.dumps(b["transactions"], sort_keys=True)

    h = calculate_hash(
        b["index"],
        b["previous_hash"],
        b["timestamp"],
        b["nonce"],
        tx_str
    )

    if h != b["hash"]:
        return False

    # difficulty check
    if not h.startswith("0" * b["difficulty"]):
        return False

    for tx in b["transactions"]:
        if not verify_tx(tx):
            return False

    return True

# =========================
# 🔥 CHAIN WORK
# =========================
def chain_work(chain):
    work = 0

    for b in chain:
        diff = b.get("difficulty", 1)
        work += 2 ** (diff * 4)

    return work

# =========================
# 🔒 FULL CHAIN VALIDATION
# =========================
def is_valid_full_chain(chain):
    try:
        # =========================
        # BASIC CHECK
        # =========================
        if not isinstance(chain, list) or len(chain) == 0:
            return False

        # =========================
        # GENESIS CHECK 🔥
        # =========================
        genesis = chain[0]

        if genesis.get("index") != 0:
            return False

        if genesis.get("previous_hash") != "0":
            return False

        # =========================
        # LOOP BLOCKS
        # =========================
        for i in range(1, len(chain)):

            b = chain[i]
            prev = chain[i - 1]

            # =========================
            # INDEX CHECK 🔢
            # =========================
            if b.get("index") != prev.get("index") + 1:
                return False

            # =========================
            # LINK CHECK 🔗
            # =========================
            if b.get("previous_hash") != prev.get("hash"):
                return False

            # =========================
            # HASH CHECK 🔐
            # =========================
            try:
                tx_str = json.dumps(b.get("transactions", []), sort_keys=True)
            except:
                return False

            h = calculate_hash(
                b.get("index"),
                b.get("previous_hash"),
                b.get("timestamp"),
                b.get("nonce"),
                tx_str
            )

            if h != b.get("hash"):
                return False

            # =========================
            # DIFFICULTY CHECK ⛏
            # =========================
            if not h.startswith("0" * b.get("difficulty", 1)):
                return False

            # =========================
            # TX VALIDATION + DOUBLE SPEND 🔥
            # =========================
            used_inputs = set()

            for tx in b.get("transactions", []):
                if not verify_tx(tx, used_inputs):
                    return False

        return True

    except Exception as e:
        print("❌ Chain validation error:", e)
        return False

def better_chain(new_chain):
    if not is_valid_full_chain(new_chain):
        return False

    local_work = chain_work(blockchain)
    new_work = chain_work(new_chain)

    if new_work > local_work * 1.1:
        return True

    return False

# =========================
# 🚀 REPLACE CHAIN (PRO VERSION)
# =========================
def replace_chain(new_chain):

    global blockchain

    if not isinstance(new_chain, list) or len(new_chain) == 0:
        return

    if not is_valid_full_chain(new_chain):
        print("❌ Invalid chain rejected")
        return

    # =========================
    # 🔥 WORK COMPARISON
    # =========================
    local_work = chain_work(blockchain)
    new_work = chain_work(new_chain)

    print(f"⚖️ Work compare → local:{local_work} | new:{new_work}")

    # =========================
    # ✅ REPLACE ONLY IF STRONGER
    # =========================
    if better_chain(new_chain):
        print("🔥 Replacing with stronger chain")

        blockchain = new_chain
        rebuild_utxo()
        save_data()

        print("✅ Chain replaced:", len(blockchain))
    else:
        print("ℹ️ Ignored weaker chain")

# ==================================================
# REQUEST PEERS (FINAL SECURE)
# ==================================================
def request_peers():
    global p2p_peers

    for peer in list(p2p_peers):
        try:
            host, port = peer.split(":")
            port = int(port)

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)

            s.connect((host, port))

            s.sendall((json.dumps({
                "type": "get_peers"
            }) + "\n").encode())

            data = s.recv(8192)

            if not data:
                continue

            try:
                resp = json.loads(data.decode())

                if resp.get("type") == "peers":

                    new_peers = resp.get("data", [])
                    seen_ips = set()

                    for p in new_peers:
                        try:
                            ip, prt = p.split(":")
                            prt = int(prt)

                            # ✅ only allowed port
                            if prt not in ALLOWED_PORTS:
                                continue

                            # 🚫 skip duplicates
                            if ip in seen_ips or ip in peer_ips:
                                continue

                            seen_ips.add(ip)

                            peer_addr = f"{ip}:{prt}"

                            if len(p2p_peers) < MAX_PEERS:
                                p2p_peers.add(peer_addr)
                                peer_ips.add(ip)
                                save_peers_safe()

                                print("🌐 Peer discovered:", peer_addr)

                        except:
                            continue

            except:
                pass

            s.close()

        except:
            continue

# ==================================================
# SAFE MULTI MESSAGE HANDLER
# ==================================================
def safe_handle(data, conn):
    messages = data.split("\n")

    for msg in messages:
        if msg.strip():
            handle_msg(msg, conn)

def send_msg(conn, data):
    try:
        if not isinstance(data, dict):
            return
        msg = json.dumps(data) + "\n"
        conn.sendall(msg.encode())
    except Exception as e:
        pass

# =========================
# 🛡 ANTI-SPAM (INBOUND)
# =========================
last_msg_time = {}

def is_spam(ip):
    now = time.time()

    last = last_msg_time.get(ip, 0)

    if now - last < 0.05:
        return True

    last_msg_time[ip] = now
    return False


# ==================================================
# HANDLE P2P MESSAGE (ULTRA PRO MAX 🚀 FINAL FIXED)
# ==================================================
recent_tx_ids = set()
recent_block_ids = set()

def handle_msg(msg, conn):

    global blockchain, p2p_peers, pending_transactions

    try:
        ip = conn.getpeername()[0]

        if is_spam(ip):
            return

        # ================= SAFE PARSE =================
        if isinstance(msg, str) and len(msg) > 100000:
            update_ip_reputation(ip, False)
            return

        try:
            data = json.loads(msg) if isinstance(msg, str) else msg
        except:
            update_ip_reputation(ip, False)
            return

        if not isinstance(data, dict):
            return

        msg_type = data.get("type")

        # ==================================================
        # 📢 INV
        # ==================================================
        if msg_type == "inv":

            request_items = []

            for item in data.get("data", []):
                typ = item.get("type")
                item_id = item.get("id")

                if not typ or not item_id:
                    continue

                if typ == "tx" and item_id not in recent_tx_ids:
                    request_items.append(item)

                elif typ == "block" and item_id not in recent_block_ids:
                    request_items.append(item)

            if request_items:
                send_msg(conn, {
                    "type": "getdata",
                    "data": request_items[:10]
                })

        # ==================================================
        # 📥 GETDATA
        # ==================================================
        elif msg_type == "getdata":

            for item in data.get("data", []):

                typ = item.get("type")
                item_id = item.get("id")

                if typ == "tx":
                    for tx in pending_transactions:
                        if tx_hash(tx) == item_id:
                            send_msg(conn, {"type": "tx", "data": tx})
                            break

                elif typ == "block":
                    for b in blockchain:
                        if b["hash"] == item_id:
                            send_msg(conn, {
                                "type": "compact_block",
                                "data": b
                            })
                            break

        # ==================================================
        # 💸 TX
        # ==================================================
        elif msg_type == "tx":

            tx = data.get("data")
            if not isinstance(tx, dict):
                return

            txid = tx_hash(tx)

            if txid in recent_tx_ids:
                return

            with mempool_lock:

                if any(tx_hash(t) == txid for t in pending_transactions):
                    return

                if not verify_tx(tx):
                    update_ip_reputation(ip, False)
                    return

                pending_transactions.append(tx)
                recent_tx_ids.add(txid)

                if len(recent_tx_ids) > 5000:
                    recent_tx_ids.clear()

            update_ip_reputation(ip, True)

            p2p_broadcast({
                "type": "inv",
                "data": [{"type": "tx", "id": txid}]
            })

        # ==================================================
        # ⚡ COMPACT BLOCK (REAL PROCESS)
        # ==================================================
        elif msg_type == "compact_block":

            block = data.get("data")
            if not isinstance(block, dict):
                return

            block_hash = block.get("hash")

            if block_hash in recent_block_ids:
                return

            if any(b["hash"] == block_hash for b in blockchain):
                return

            # 🔥 fork detect
            if blockchain and block.get("previous_hash") != blockchain[-1]["hash"]:
                print("⚠️ Fork detected → syncing...")
                request_chain()
                return

            # ================= VALIDATE =================
            tx_str = json.dumps(block["transactions"], sort_keys=True)

            calc_hash = calculate_hash(
                block["index"],
                block["previous_hash"],
                block["timestamp"],
                block["nonce"],
                tx_str
            )

            if calc_hash != block_hash:
                update_ip_reputation(ip, False)
                return

            if not calc_hash.startswith("0" * block.get("difficulty", 1)):
                return

            # ================= TX VALIDATION =================
            used_inputs = set()
            for tx in block.get("transactions", []):
                if not verify_tx(tx, used_inputs):
                    return

            # ================= ADD =================
            with blockchain_lock:
                blockchain.append(block)
                update_utxo(block)

            recent_block_ids.add(block_hash)

            save_data()

            # 🔥 notify network (INV only)
            p2p_broadcast({
                "type": "inv",
                "data": [{"type": "block", "id": block_hash}]
            })

            print(f"✅ Block {block['index']} accepted")

        # ==================================================
        # 🔄 GET HEADERS
        # ==================================================
        elif msg_type == "get_headers":

            send_msg(conn, {
                "type": "headers",
                "data": get_block_headers(blockchain[-500:])
            })

        # ==================================================
        # 📊 HEADERS
        # ==================================================
        elif msg_type == "headers":

            headers = data.get("data", [])
            print("📊 Headers received:", len(headers))

            if headers and len(headers) > len(blockchain):
                print("⚡ Need sync → requesting chain")
                request_chain()

        # ==================================================
        # 🔄 GET CHAIN
        # ==================================================
        elif msg_type == "get_chain":

            send_msg(conn, {
                "type": "chain",
                "data": blockchain[-300:]
            })

        # ==================================================
        # 🔄 CHAIN
        # ==================================================
        elif msg_type == "chain":

            new_chain = data.get("data")

            if isinstance(new_chain, list) and len(new_chain) > len(blockchain):
                if is_valid_full_chain(new_chain):

                    print("🔄 Chain replaced (LONGER VALID)")

                    with blockchain_lock:
                        blockchain.clear()
                        blockchain.extend(new_chain)

                    rebuild_utxo()
                    save_data()

        # ==================================================
        # 🤝 HELLO
        # ==================================================
        elif msg_type == "hello":

            port = int(data.get("port", 0))

            if port not in ALLOWED_PORTS:
                return

            peer = f"{ip}:{port}"

            if len(p2p_peers) < MAX_PEERS:
                p2p_peers.add(peer)
                peer_ips.add(ip)
                save_peers_safe()

            send_msg(conn, {
                "type": "peers",
                "data": list(p2p_peers)[:50]
            })

        # ==================================================
        # 🌐 PEERS
        # ==================================================
        elif msg_type == "peers":

            for p in data.get("data", []):
                try:
                    ip2, port = p.split(":")
                    port = int(port)

                    if port not in ALLOWED_PORTS:
                        continue

                    if len(p2p_peers) < MAX_PEERS:
                        p2p_peers.add(f"{ip2}:{port}")

                except:
                    continue

        # ==================================================
        # ❤️ PING / PONG
        # ==================================================
        elif msg_type == "ping":
            send_msg(conn, {"type": "pong"})

        elif msg_type == "pong":
            mark_peer_alive(f"{ip}:{P2P_PORT}")

    except Exception as e:
        print("P2P error:", e)

# ==================================================
# REQUEST CHAIN
# ==================================================
def request_chain():

    for peer in list(p2p_peers):

        try:
            ip, port = peer.split(":")
            port = int(port)

            s = socket.socket()
            s.settimeout(5)

            s.connect((ip, port))

            s.sendall((json.dumps({
                "type": "get_chain"
            }) + "\n").encode())

            data = s.recv(100000)  # 🔥 muhiim

            if data:
                safe_handle(data.decode(), s)

            s.close()

        except:
            pass

def sync_headers():
    for peer in list(p2p_peers):
        try:
            ip, port = peer.split(":")
            s = socket.socket()
            s.settimeout(3)
            s.connect((ip, int(port)))

            s.sendall((json.dumps({
                "type": "get_headers"
            }) + "\n").encode())

            data = s.recv(100000)

            if data:
                msg = json.loads(data.decode())
                handle_msg(msg, s)

            s.close()
        except:
            pass


# =========================
# PING PEERS (KEEP ALIVE 🔥)
# =========================
def ping_peers():
    while True:
        for peer in list(p2p_peers):
            try:
                ip, port = peer.split(":")
                s = socket.socket()
                s.settimeout(2)
                s.connect((ip, int(port)))

                s.sendall((json.dumps({"type": "ping"}) + "\n").encode())
                s.close()

                mark_peer_alive(peer)

            except:
                punish_peer(peer)

        time.sleep(15)

# =========================
# AUTO MEMPOOL CLEAN
# =========================
def auto_clean_mempool():
    while True:
        try:
            clean_mempool()
        except Exception as e:
            print("Mempool clean error:", e)

        time.sleep(30)  # every 30 sec

# ==================================================
# NODE ID (PRO VERSION - CRYPTO IDENTITY)
# ==================================================
from ecdsa import SigningKey, SECP256k1
import hashlib
import os

NODE_KEY_FILE = "node_key.pem"

# =========================
# GENERATE KEYS
# =========================
def generate_node_keys():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()

    # 🔒 save private key securely
    with open(NODE_KEY_FILE, "wb") as f:
        f.write(sk.to_pem())

    try:
        os.chmod(NODE_KEY_FILE, 0o600)  # owner only
    except:
        pass

    return sk, vk

# =========================
# LOAD KEYS
# =========================
def load_node_keys():
    with open(NODE_KEY_FILE, "rb") as f:
        sk = SigningKey.from_pem(f.read())

    vk = sk.get_verifying_key()
    return sk, vk

# =========================
# LOAD OR CREATE KEYS
# =========================
try:
    if os.path.exists(NODE_KEY_FILE):
        node_sk, node_vk = load_node_keys()
    else:
        node_sk, node_vk = generate_node_keys()
except Exception as e:
    print("⚠️ Key error → regenerating:", e)
    node_sk, node_vk = generate_node_keys()

# =========================
# PUBLIC KEY
# =========================
NODE_PUBLIC_KEY = node_vk.to_string().hex()

# =========================
# NODE ID = HASH(PUBLIC KEY)
# =========================
NODE_ID = hashlib.sha256(
    NODE_PUBLIC_KEY.encode()
).hexdigest()

# =========================
# SIGN FUNCTION (IMPORTANT)
# =========================
def sign_message(message):
    h = hashlib.sha256(message.encode()).digest()
    return node_sk.sign(h).hex()

# ==================================================
# CONNECT TO SEED NODES (FINAL PRO VERSION)
# ==================================================
def connect_seed_nodes():

    for seed in SEED_NODES:

        try:
            host, port = seed.split(":")
            port = int(port)

            # allow only valid ports
            if port not in ALLOWED_PORTS:
                continue

            s = socket.socket()
            s.settimeout(5)

            s.connect((host, port))

            # ✅ FULL SECURE HELLO (FIXED)
            s.sendall((json.dumps({
                "type": "hello",
                "port": P2P_PORT,
                "node_id": NODE_ID,
                "public_key": NODE_PUBLIC_KEY,
                "signature": sign_message(NODE_ID)
            }) + "\n").encode())

            # ✅ allow multiple ports per IP
            peer = f"{host}:{port}"

            if peer not in p2p_peers:
                p2p_peers.add(peer)
                peer_ips.add(host)
                save_peers_safe()

            print("Connected to seed:", seed)
            save_data()
        except Exception as e:
            print("Seed failed:", seed, "|", e)

        finally:
            try:
                s.close()
            except:
                pass


def random_bootstrap():
    if not p2p_peers:
        return  # ❗ avoid crash haddii peers jiro la'aan

    for peer in random.sample(list(p2p_peers), min(5, len(p2p_peers))):
        try:
            ip, port = peer.split(":")
            s = socket.socket()
            s.settimeout(3)
            s.connect((ip, int(port)))

            s.sendall((json.dumps({
                "type": "hello",
                "port": P2P_PORT,
                "node_id": NODE_ID,
                "public_key": NODE_PUBLIC_KEY,
                "signature": sign_message(NODE_ID)
            }) + "\n").encode())

            s.close()
        except:
            pass

# ==================================================
# 🚀 START BACKGROUND SERVICES (ULTRA PRO MAX)
# ==================================================

def start_background_services():

    print("🚀 Starting background services...")

    # 🌐 Network sync
    threading.Thread(target=sync_headers, daemon=True).start()

    # 🔄 Peer rotation (keep best peers only)
    threading.Thread(target=rotate_peers, daemon=True).start()

    # 🧹 Remove dead peers
    threading.Thread(target=clean_dead_peers, daemon=True).start()

    # ❤️ Keep peers alive
    threading.Thread(target=ping_peers, daemon=True).start()

    # 🔍 Discover new peers
    threading.Thread(target=smart_discovery, daemon=True).start()

    # 📡 Share peers with network
    threading.Thread(target=gossip_peers, daemon=True).start()

    # 🌍 DNS bootstrap
    threading.Thread(target=dns_bootstrap, daemon=True).start()

    # 🧠 Ensure minimum peers (auto recovery)
    threading.Thread(target=ensure_minimum_peers, daemon=True).start()

    # 🌱 Auto expand seeds
    threading.Thread(target=auto_seed_expand, daemon=True).start()

    # ⚖️ Smart seed control
    threading.Thread(target=auto_seed_control, daemon=True).start()

    # 🧼 Clean mempool
    threading.Thread(target=auto_clean_mempool, daemon=True).start()

    print("✅ All background services started")

# ==================================================
# P2P SERVER (FINAL PRO - ULTRA STABLE + SECURE 🔥)
# ==================================================
def p2p_server():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind(("0.0.0.0", P2P_PORT))
    s.listen(100)

    print("📡 P2P server running on port", P2P_PORT)

    while True:
        conn, addr = s.accept()
        peer_ip = addr[0]

        # =========================================
        # 🚫 BLOCK INVALID IPS
        # =========================================
        if (
            peer_ip.startswith("127.") or
            peer_ip.startswith("0.") or
            peer_ip.startswith("255.") or
            peer_ip == "0.0.0.0"
        ):
            conn.close()
            continue

        # =========================================
        # 🚫 BANNED IPS
        # =========================================
        if peer_ip in banned_ips:
            conn.close()
            continue

        # =========================================
        # CLIENT THREAD
        # =========================================
        def client_thread(c, addr):

            ip = addr[0]

            try:
                c.settimeout(15)
                buffer = ""

                while True:
                    try:
                        data = c.recv(4096)
                    except:
                        break

                    if not data:
                        break

                    # =========================
                    # SAFE DECODE
                    # =========================
                    try:
                        buffer += data.decode(errors="ignore")
                    except:
                        continue

                    # =========================
                    # MULTI MESSAGE PARSER
                    # =========================
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)

                        if not line.strip():
                            continue

                        # =========================
                        # FORMAT CHECK
                        # =========================
                        if not (line.startswith("{") and line.endswith("}")):
                            continue

                        # =========================
                        # SIZE LIMIT (ANTI-SPAM)
                        # =========================
                        if len(line) > 100000:
                            update_ip_reputation(ip, False)
                            continue

                        # =========================
                        # SAFE JSON PARSE
                        # =========================
                        try:
                            msg = json.loads(line)
                        except:
                            update_ip_reputation(ip, False)
                            continue

                        if not isinstance(msg, dict):
                            continue

                        msg_type = msg.get("type")

                        # =========================
                        # 🔒 ALLOWED MESSAGE TYPES (FULL 🔥)
                        # =========================
                        if msg_type not in [
                            "hello",
                            "tx",
                            "block",
                            "inv",
                            "getdata",
                            "get_headers",
                            "headers",
                            "compact_block",
                            "get_chain",
                            "chain",
                            "get_peers",
                            "peers",
                            "ping",
                            "pong"
                        ]:
                            continue

                        # =========================
                        # 🚫 SPAM CHECK
                        # =========================
                        if is_spam(ip):
                            continue

                        # =========================
                        # HANDLE MESSAGE
                        # =========================
                        try:
                            handle_msg(msg, c)
                        except Exception as e:
                            print("⚠️ Handle error:", e)
                            update_ip_reputation(ip, False)

            except Exception as e:
                # silent
                pass

            finally:
                try:
                    c.close()
                except:
                    pass

        # =========================================
        # THREAD PER CONNECTION
        # =========================================
        threading.Thread(
            target=client_thread,
            args=(conn, addr),
            daemon=True
        ).start()


# ==================================================
# ADDRESS INFO (BALANCE + UTXO + HISTORY)
# ==================================================
@app.route("/address/<wallet>")
def address_info(wallet):

    balance = 0
    utxos = []
    history = []

    # =========================
    # UTXO BALANCE
    # =========================
    for utxo_id, utxo in utxo_set.items():

        if utxo["address"] == wallet:

            balance += utxo["amount"]

            utxos.append({
                "utxo": utxo_id,
                "amount": utxo["amount"]
            })

    # =========================
    # TX HISTORY
    # =========================
    for block in blockchain:

        for tx in block["transactions"]:

            # received coins
            for out in tx.get("outputs", []):
                if out["address"] == wallet:

                    history.append({
                        "type": "receive",
                        "amount": out["amount"],
                        "block": block["index"]
                    })

            # sent coins
            if tx.get("sender") == wallet:

                for out in tx.get("outputs", []):
                    history.append({
                        "type": "send",
                        "amount": out["amount"],
                        "block": block["index"]
                    })

    return jsonify({
        "address": wallet,
        "balance": balance,
        "utxos": utxos,
        "history": history
    })

# ==================================================
# TX HISTORY (SIMPLE + WALLET READY)
# ==================================================
@app.route("/txs/<address>")
def get_txs(address):

    txs = []

    for block in blockchain:

        for i, tx in enumerate(block["transactions"]):

            txid = block["hash"] + str(i)

            # SEND
            if tx.get("sender") == address:
                txs.append({
                    "type": "send",
                    "amount": sum(out["amount"] for out in tx.get("outputs", []) if out["address"] != address),
                    "to": [out["address"] for out in tx.get("outputs", []) if out["address"] != address],
                    "block": block["index"],
                    "txid": txid
                })

            # RECEIVE
            for out in tx.get("outputs", []):
                if out["address"] == address:
                    txs.append({
                        "type": "receive",
                        "amount": out["amount"],
                        "from": tx.get("sender"),
                        "block": block["index"],
                        "txid": txid
                    })

    return jsonify({
        "address": address,
        "txs": txs[::-1]  # latest first
    })


# ==================================================
# GLOBAL LOCKS + STATE
# ==================================================
mining_lock = threading.Lock()
blockchain_lock = threading.Lock()
mempool_lock = threading.Lock()

last_mine_time = 0
MINE_COOLDOWN = 1.5   # anti spam


# ==================================================
# MINE (REAL + CLEAN + PRO 🚀)
# ==================================================

@app.route("/mine/<addr>")
def mine(addr):

    global pending_transactions, last_mine_time

    # =========================================
    # VALIDATION
    # =========================================
    if not addr.startswith("SOM") or len(addr) < 10:
        return jsonify({"error": "invalid address"})

    # =========================================
    # RATE LIMIT
    # =========================================
    now = time.time()
    if now - last_mine_time < MINE_COOLDOWN:
        return jsonify({"status": "cooldown"})

    last_mine_time = now

    # =========================================
    # SINGLE MINER LOCK
    # =========================================
    if not mining_lock.acquire(blocking=False):
        return jsonify({"status": "already mining"})

    try:
        # =========================================
        # GENESIS CHECK
        # =========================================
        if len(blockchain) == 0:
            create_genesis()

        # =========================================
        # 🛑 MAX SUPPLY STOP (🔥 muhiim)
        # =========================================
        if block_reward() <= 0:
            return jsonify({
                "status": "max supply reached",
                "supply": total_supply()
            })

        # =========================================
        # MEMPOOL SNAPSHOT
        # =========================================
        with mempool_lock:
            mempool_snapshot = list(pending_transactions)

        # =========================================
        # SELECT TX (FEE PRIORITY)
        # =========================================
        valid_txs = []

        for tx in sorted(mempool_snapshot, key=lambda x: x.get("fee", 0), reverse=True):
            try:
                if tx.get("sender") == "NETWORK":
                    continue

                if verify_tx(tx):
                    valid_txs.append(tx)

                if len(valid_txs) >= MAX_TX_PER_BLOCK:
                    break

            except:
                continue

        # =========================================
        # REWARD (BLOCK + FEES)
        # =========================================
        total_fees = sum(float(tx.get("fee", 0)) for tx in valid_txs)

        base_reward = block_reward()
        reward_amount = round(base_reward + total_fees, 8)

        # safety check
        if reward_amount <= 0:
            return jsonify({"status": "no reward"})

        # =========================================
        # COINBASE TX
        # =========================================
        coinbase_tx = {
            "sender": "NETWORK",
            "inputs": [],
            "outputs": [{
                "address": addr,
                "amount": reward_amount
            }],
            "timestamp": time.time()
        }

        block_txs = [coinbase_tx] + valid_txs

        # =========================================
        # CHAIN STATE
        # =========================================
        with blockchain_lock:
            last_block = blockchain[-1]
            index = last_block["index"] + 1
            prev_hash = last_block["hash"]
            difficulty = dynamic_difficulty()

        print(f"⛏ Mining block {index} | diff={difficulty}")

        # =========================================
        # MULTI CPU MINING
        # =========================================
        cpu_count = multiprocessing.cpu_count()

        with multiprocessing.Pool(cpu_count) as pool:

            jobs = [
                pool.apply_async(
                    mine_worker,
                    (i, cpu_count, index, prev_hash, block_txs, difficulty)
                )
                for i in range(cpu_count)
            ]

            nonce = None
            timestamp = None
            mined_hash = None

            while True:

                with blockchain_lock:
                    if blockchain[-1]["hash"] != prev_hash:
                        pool.terminate()
                        pool.join()
                        return jsonify({"error": "chain changed"})

                for job in jobs:
                    if job.ready():
                        result = job.get()
                        if result:
                            nonce, timestamp, mined_hash = result
                            break

                if nonce is not None:
                    pool.terminate()
                    pool.join()
                    break

                time.sleep(0.01)

        # =========================================
        # BUILD BLOCK
        # =========================================
        block = {
            "index": index,
            "timestamp": timestamp,
            "transactions": block_txs,
            "nonce": nonce,
            "previous_hash": prev_hash,
            "difficulty": difficulty,
            "hash": mined_hash
        }

        # =========================================
        # VALIDATE + ADD
        # =========================================
        with blockchain_lock:

            if not validate_block(block, blockchain):
                return jsonify({"error": "invalid block"})

            blockchain.append(block)
            update_utxo(block)

        # =========================================
        # CLEAN MEMPOOL
        # =========================================
        with mempool_lock:
            pending_transactions[:] = [
                tx for tx in pending_transactions if tx not in valid_txs
            ]

        # =========================================
        # SAVE
        # =========================================
        save_data()

        # =========================================
        # BROADCAST
        # =========================================
        try:
            p2p_broadcast({
                "type": "block",
                "data": block
            })
        except Exception as e:
            print("⚠️ Broadcast error:", e)

        print(f"✅ BLOCK MINED: {index} | {mined_hash}")

        return jsonify({
            "status": "block mined",
            "block": index,
            "hash": mined_hash,
            "reward": reward_amount,
            "txs": len(block_txs)
        })

    except Exception as e:
        print("❌ Mining error:", e)
        return jsonify({"error": str(e)})

    finally:
        if mining_lock.locked():
            mining_lock.release()

# ==================================================
# GLOBAL STATE
# ==================================================
auto_mining = False
auto_miner_thread = None


def compact_block(block):
    return {
        "index": block["index"],
        "hash": block["hash"],
        "previous_hash": block["previous_hash"],
        "tx_ids": [tx_hash(tx) for tx in block["transactions"]],
        "timestamp": block["timestamp"],
        "difficulty": block["difficulty"]
    }

# ==================================================
# 📊 BLOCK HEADERS (FAST SYNC 🔥)
# ==================================================
def get_block_headers(chain):
    headers = []

    for b in chain:
        headers.append({
            "index": b["index"],
            "hash": b["hash"],
            "previous_hash": b["previous_hash"],
            "timestamp": b["timestamp"],
            "difficulty": b.get("difficulty", 1)
        })

    return headers

# ==================================================
# P2P BROADCAST
# ==================================================
import random

recent_messages = set()

def p2p_broadcast(msg):

    try:
        msg_id = hashlib.sha256(json.dumps(msg, sort_keys=True).encode()).hexdigest()

        # 🚫 avoid rebroadcast spam
        if msg_id in recent_messages:
            return

        recent_messages.add(msg_id)

        # limit memory
        if len(recent_messages) > 5000:
            recent_messages.clear()

    except:
        pass

    data = (json.dumps(msg) + "\n").encode()

    # 🔥 mix best + random (IMPORTANT)
    best = get_best_peers(MAX_ACTIVE_BROADCAST // 2)
    random_peers = random.sample(
        list(p2p_peers),
        min(MAX_ACTIVE_BROADCAST // 2, len(p2p_peers))
    )

    peers = list(set(best + random_peers))

    for peer in peers:
        try:
            ip, port = peer.split(":")
            s = socket.socket()
            s.settimeout(2)
            s.connect((ip, int(port)))

            s.sendall(data)
            s.close()

            reward_peer(peer)

        except:
            punish_peer(peer)

# ==================================================
# 🌍 PUBLIC IP (REAL + STABLE + CACHED)
# ==================================================
import requests
import time
import os
import random
import threading

_cached_ip = None
_last_ip_check = 0

def get_public_ip():
    global _cached_ip, _last_ip_check

    # ⏱ refresh every 5 min
    if _cached_ip and time.time() - _last_ip_check < 300:
        return _cached_ip

    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://ipinfo.io/ip"
    ]

    for url in services:
        try:
            ip = requests.get(url, timeout=3).text.strip()

            # basic validation
            if ip and len(ip) < 50 and "." in ip:
                _cached_ip = ip
                _last_ip_check = time.time()
                print("🌍 Public IP:", ip)
                return ip

        except:
            continue

    return "127.0.0.1"


# ✅ FINAL NODE IP
NODE_IP = os.getenv("NODE_IP", get_public_ip())


# ==================================================
# HTTP BLOCK RECEIVE (ULTRA PRO - FINAL VERSION 🚀🔥)
# ==================================================
@app.route("/receive_block", methods=["POST"])
def receive_block_http():

    global blockchain, pending_transactions, p2p_peers

    try:
        b = request.json

        # =========================
        # BASIC VALIDATION
        # =========================
        if not b or not isinstance(b, dict):
            return {"status": "bad_request"}

        required = ["index", "hash", "previous_hash", "transactions"]

        if not all(k in b for k in required):
            return {"status": "bad_format"}

        # =========================
        # CHAIN EMPTY CHECK
        # =========================
        if len(blockchain) == 0:
            return {"status": "no_chain"}

        # =========================
        # DUPLICATE CHECK
        # =========================
        if any(block["hash"] == b["hash"] for block in blockchain):
            return {"status": "duplicate"}

        last_block = blockchain[-1]

        # =========================
        # 🚨 ANTI-FORK (SMART SYNC)
        # =========================
        if b["previous_hash"] != last_block["hash"]:

            print("⚠️ Out of sync → syncing headers (FAST)...")

            # 🔥 FAST SYNC (instead of heavy chain)
            try:
                threading.Thread(target=sync_headers, daemon=True).start()
            except:
                threading.Thread(target=request_chain, daemon=True).start()

            return {"status": "syncing"}

        # =========================
        # VALIDATE BLOCK
        # =========================
        if not validate_block(b, blockchain):
            print("❌ Invalid block rejected")
            return {"status": "invalid"}

        # =========================
        # ADD BLOCK (LOCK SAFE)
        # =========================
        with blockchain_lock:
            blockchain.append(b)

            try:
                update_utxo(b)
            except:
                print("⚠️ UTXO error → rebuilding...")
                rebuild_utxo()

        # =========================
        # CLEAN MEMPOOL
        # =========================
        try:
            tx_hashes = {tx_hash(tx) for tx in b["transactions"]}

            with mempool_lock:
                pending_transactions[:] = [
                    tx for tx in pending_transactions
                    if tx_hash(tx) not in tx_hashes
                ]
        except:
            pass

        # =========================
        # SAVE DATA
        # =========================
        try:
            save_data()
        except Exception as e:
            print("⚠️ Save error:", e)

        # =========================
        # P2P BROADCAST (SAFE)
        # =========================
        try:
            p2p_broadcast({
                "type": "block",
                "data": b
            })
        except Exception as e:
            print("⚠️ Broadcast error:", e)

        # =========================
        # 🔥 SMART RELAY (ANTI-SPAM + FAST)
        # =========================
        def relay_block(peer, block):
            try:
                ip = peer.split(":")[0]

                # ❌ skip self
                if ip == NODE_IP:
                    return

                url = f"http://{ip}:9443/receive_block"

                requests.post(url, json=block, timeout=2)

            except requests.exceptions.Timeout:
                pass

            except requests.exceptions.ConnectionError:
                p2p_peers.discard(peer)
                print(f"❌ Dead peer removed: {peer}")

            except Exception as e:
                print("Relay error:", e)

        # =========================
        # GOSSIP (MIX BEST + RANDOM)
        # =========================
        try:
            peers = list(p2p_peers)

            if peers:
                random.shuffle(peers)

                # 🔥 max 8 peers (anti spam)
                selected = peers[:8]

                for peer in selected:
                    threading.Thread(
                        target=relay_block,
                        args=(peer, b),
                        daemon=True
                    ).start()
        except:
            pass

        print(f"✅ BLOCK ACCEPTED: {b['index']}")

        return {"status": "accepted"}

    except Exception as e:
        print("❌ Receive block fatal error:", e)
        return {"status": "error"}


# ==================================================
# API INFO
# ==================================================
@app.route("/api")
def api():
    return jsonify({
        "network": NETWORK_NAME,
        "creator": CREATOR,
        "year": CREATED_YEAR,
        "blocks": len(blockchain),
        "mempool": len(pending_transactions),
        "peers": len(p2p_peers),
        "difficulty": get_new_difficulty(blockchain),
        "supply": total_supply(),        # ✅ comma muhiim ah
        "hashrate": calculate_hashrate()
    })

@app.route("/fee")
def fee_api():
    return jsonify({
        "recommended_fee": get_recommended_fee(),
        "mempool_size": len(pending_transactions)
    })

@app.route("/get_block_template")
def get_block_template():

    if len(blockchain) == 0:
        return {"error": "no chain"}

    last_block = blockchain[-1]

    # =========================
    # BUILD TX LIST
    # =========================
    with mempool_lock:
        txs = pending_transactions[:MAX_TX_PER_BLOCK]

    # =========================
    # MERKLE ROOT (SIMPLE)
    # =========================
    tx_hashes = [
        hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()
        for tx in txs
    ]

    merkle = hashlib.sha256("".join(tx_hashes).encode()).hexdigest() if tx_hashes else "0"*64

    # =========================
    # BLOCK HEADER
    # =========================
    header = {
        "index": last_block["index"] + 1,
        "prev_hash": last_block["hash"],
        "merkle_root": merkle,
        "timestamp": int(time.time()),
        "difficulty": get_new_difficulty(blockchain)
    }

    return header

@app.route("/get_job")
def get_job():
    try:
        template = requests.get("http://127.0.0.1:9443/get_block_template").json()

        if "error" in template:
            return {"error": "no template"}

        global block_header

        block_header = (
            str(template["index"]) +
            template["prev_hash"] +
            str(template["timestamp"]) +
            template["merkle_root"]
        )

        return jsonify({
            "index": template["index"],
            "prev_hash": template["prev_hash"],
            "difficulty": template["difficulty"],
            "header": block_header
        })

    except Exception as e:
        return {"error": str(e)}

# ==================================================
# GET BLOCK BY HEIGHT
# ==================================================
@app.route("/block/<int:height>")
def get_block(height):
    if height < len(blockchain):
        block = blockchain[height]
        return jsonify({
            "height": height,
            "hash": block["hash"],
            "previous": block["previous_hash"],
            "nonce": block["nonce"],
            "time": block["timestamp"],
            "tx": block["transactions"]
        })
    else:
        return jsonify({"error": "block not found"}), 404

# ==================================================
# FULL CHAIN
# ==================================================
@app.route("/chain")
def chain_api():
    return jsonify({
        "blocks": len(blockchain),
        "chain": blockchain
    })


# ==================================================
# MEMPOOL
# ==================================================
@app.route("/mempool")
def mempool_api():
    return jsonify(pending_transactions)


# ==================================================
# STATS
# ==================================================
@app.route("/stats")
def stats_api():

    blocks = len(blockchain)
    mempool = len(pending_transactions)

    return jsonify({
        "network": NETWORK_NAME,
        "blocks": blocks,
        "mempool": mempool,
        "difficulty": difficulty,
        "supply": total_supply()
    })

# ==================================================
# BLOCK BY HEIGHT
# ==================================================
@app.route("/api/block/<int:index>")
def block_by_height(index):

    if index < 0 or index >= len(blockchain):
        return jsonify({"error": "block not found"})

    return jsonify(blockchain[index])


# ==================================================
# ADDRESS BALANCE (UTXO MODEL)
# ==================================================
@app.route("/balance/<address>")
def balance_api(address):

    bal = 0

    for utxo in utxo_set.values():
        if utxo["address"] == address:
            bal += utxo["amount"]

    return jsonify({
        "address": address,
        "balance": bal
    })


# ==================================================
# RICH LIST (UTXO BASED - FIXED)
# ==================================================
@app.route("/richlist")
def richlist():

    balances = {}

    # 🔥 UTXO BASED (REAL BALANCE)
    for utxo in utxo_set.values():

        addr = utxo["address"]
        amount = utxo["amount"]

        balances[addr] = balances.get(addr, 0) + amount

    # 🔽 sort richest first
    rich = sorted(balances.items(), key=lambda x: x[1], reverse=True)

    result = []
    for addr, bal in rich[:100]:
        if bal > 0:
            result.append({
                "address": addr,
                "balance": round(bal, 8)
            })

    return jsonify(result)


# ==================================================
# TRANSACTION LOOKUP
# ==================================================

@app.route("/tx/<txid>")
def get_transaction(txid):

    for block in blockchain:
        for i, tx in enumerate(block["transactions"]):

            generated_txid = block["hash"] + str(i)

            if generated_txid == txid:
                return jsonify({
                    "txid": generated_txid,
                    "block": block["index"],
                    "block_hash": block["hash"],
                    "timestamp": block["timestamp"],
                    "transaction": tx
                })

    return jsonify({"error": "transaction not found"})


# ==================================================
# TRANSACTION SEARCH
# ==================================================

@app.route("/api/search")
def search():

    q = request.args.get("q")

    if not q:
        return jsonify({"error": "missing query"})

    # SEARCH BLOCK
    if q.isdigit():

        i = int(q)

        if i < len(blockchain):
            return jsonify({
                "type": "block",
                "data": blockchain[i]
            })

    # SEARCH TRANSACTION
    for block in blockchain:
        for i, tx in enumerate(block["transactions"]):

            txid = block["hash"] + str(i)

            if q == txid:
                return jsonify({
                    "type": "transaction",
                    "block": block["index"],
                    "txid": txid,
                    "transaction": tx
                })

    # SEARCH ADDRESS
    history = []

    for block in blockchain:
        for tx in block["transactions"]:

            if tx.get("sender") == q or tx.get("receiver") == q:

                history.append({
                    "block": block["index"],
                    "tx": tx
                })

    if history:
        return jsonify({
            "type": "address",
            "history": history
        })

    return jsonify({"error": "not found"})


# ==================================================
# WALLET UI
# ==================================================

@app.route("/")
def home():
    return render_template("wallet.html")

@app.route("/wallet")
def wallet():
    return render_template("wallet.html")



# ==================================================
# 📥 RECEIVE PEERS (SECURE)
# ==================================================
@app.route("/peers", methods=["POST"])
def receive_peers():

    data = request.json
    new_peers = data.get("peers", [])

    added = 0

    for peer in new_peers:
        try:
            ip, port = peer.split(":")
            port = int(port)

            if port not in ALLOWED_PORTS:
                continue

            if ip.startswith("127.") or ip == "0.0.0.0":
                continue

            if ip in banned_ips:
                continue

            clean_peer = f"{ip}:{port}"

            if clean_peer not in p2p_peers:
                p2p_peers.add(clean_peer)
                peer_scores[clean_peer] = 0
                added += 1
                save_peers_safe()

        except:
            continue

    if added:
        print(f"🌍 Added {added} peers")

    return {"status": "ok", "added": added}


# ==================================================
# 📤 GET PEERS (FOR NETWORK)
# ==================================================
@app.route("/peers", methods=["GET"])
def get_peers_api():
    return jsonify({
        "peers": list(p2p_peers)[:100]
    })


# ==================================================
# 🧹 REMOVE BAD PEERS (ANTI-SPAM)
# ==================================================
def clean_bad_peers():
    while True:
        try:
            for peer, score in list(peer_scores.items()):
                if score < -3:
                    print("🚫 Removing bad peer:", peer)
                    p2p_peers.discard(peer)
                    peer_scores.pop(peer, None)

        except Exception as e:
            print("Clean error:", e)

        time.sleep(30)

def clean_peer_ips():
    while True:
        try:
            active_ips = set()

            for peer in p2p_peers:
                ip = peer.split(":")[0]
                active_ips.add(ip)

            # keep only active IPs
            peer_ips.intersection_update(active_ips)

        except Exception as e:
            print("Peer IP clean error:", e)

        time.sleep(60)

# =========================
# 🔄 PEER ROTATION
# =========================
def rotate_peers():
    while True:
        try:
            if len(p2p_peers) > MAX_ACTIVE_PEERS:
                weakest = sorted(
                    p2p_peers,
                    key=lambda p: peer_scores.get(p, 0)
                )[:10]

                for p in weakest:
                    p2p_peers.discard(p)

        except Exception as e:
            print("Rotate error:", e)

        time.sleep(20)

# ==================================================
# 🌱 SEED NODES (REAL NETWORK BASE)
# ==================================================

def load_seed_nodes():
    for seed in SEED_NODES:
        if seed not in p2p_peers:
            p2p_peers.add(seed)
            peer_scores[seed] = 10  # 🔥 trusted

# =========================
# 🔄 AUTO SYNC (REAL)
# =========================
def auto_sync():
    while True:
        try:
            best_chain = blockchain
            best_work = chain_work(blockchain)

            for peer in list(p2p_peers):
                try:
                    res = requests.get(f"http://{peer}/chain", timeout=3)
                    data = res.json()

                    peer_chain = data.get("chain", [])

                    # 🔒 VALIDATE
                    if is_valid_full_chain(peer_chain):

                        peer_work = chain_work(peer_chain)

                        if peer_work > best_work:
                            print(f"⬇️ Better chain from {peer} (work={peer_work})")
                            best_chain = peer_chain
                            best_work = peer_work

                except:
                    continue

            # 🔥 UPDATE haddii work ka fiican yahay
            if best_work > chain_work(blockchain):
                print("🔥 Syncing to strongest chain...")
                replace_chain(best_chain)

        except Exception as e:
            print("Auto sync error:", e)

        time.sleep(5)


# =========================
# 🧱 ORPHAN SYSTEM
# =========================
orphan_blocks = []

def orphan_blocks_count():
    return len(orphan_blocks)


# =========================
# 🔧 ORPHAN FIX
# =========================
def auto_resolve_orphans():
    while True:
        try:
            if len(p2p_peers) < 2:
                time.sleep(5)
                continue

            if orphan_blocks_count() > 3:
                print("⚠️ Too many orphans → sync")
                request_chain()

        except Exception as e:
            print("Orphan fix error:", e)

        time.sleep(10)

# =========================
# BACKGROUND SYSTEM (PRO)
# =========================
def background_init():
    print("⚙️ Background system started")

    while True:
        try:
            # 1. Check blockchain health
            if len(blockchain) == 0:
                print("⚠️ Chain empty → fixing...")
                create_genesis()

            # 2. Ensure peers
            if len(p2p_peers) < 2:
                print("⚠️ Low peers → reconnecting...")
                random_bootstrap()

            # 3. Memory cleanup
            if len(pending_transactions) > MAX_MEMPOOL:
                clean_mempool()
                pending_transactions.clear()

        except Exception as e:
            print("Background error:", e)

        time.sleep(15)

# ================================================
# 🚀 START NODE (FINAL PRO - CLEAN + DECENTRALIZED)
# ================================================
if __name__ == "__main__":

    import os
    import threading
    import time
    import requests

    # =========================
    # CONFIG
    # =========================
    HTTP_PORT = int(os.environ.get("PORT", 9443))
    P2P_PORT = int(os.environ.get("P2P_PORT", 9334))

    print("🚀 Starting SomCoin node (PRO MODE)...")

    # =========================
    # SAFE THREAD STARTER
    # =========================
    def start_thread(target, name):
        def wrapper():
            while True:
                try:
                    target()
                except Exception as e:
                    print(f"💥 {name} crashed:", e)
                    time.sleep(3)

        t = threading.Thread(target=wrapper, daemon=True)
        t.start()
        print(f"✅ {name} started")

    # =========================
    # LOAD DATA
    # =========================
    try:
        load_data()
    except Exception as e:
        print("❌ Load error:", e)

    if not blockchain:
        print("⚠️ Creating genesis...")
        create_genesis()

    try:
        rebuild_utxo()
    except Exception as e:
        print("❌ UTXO error:", e)

    # =========================
    # 🌐 CORE NETWORK (ONLY IMPORTANT 🔥)
    # =========================
    start_thread(p2p_server, "P2P Server")
    start_thread(dns_bootstrap, "DNS Discovery")

    start_thread(smart_discovery, "Peer Discovery")
    start_thread(ensure_minimum_peers, "Peer Recovery")
    start_thread(rotate_peers, "Peer Rotation")
    start_thread(auto_seed_control, "Auto Seed Control")

    start_thread(auto_sync, "Auto Sync (CONSENSUS)")
    start_thread(ping_peers, "Peer KeepAlive")

    # =========================
    # 🧹 CLEAN SYSTEM
    # =========================
    start_thread(auto_clean_mempool, "Mempool Cleaner")
    start_thread(clean_bad_peers, "Bad Peer Cleaner")
    start_thread(clean_peer_ips, "Peer IP Cleaner")
    start_thread(clean_dead_peers, "Dead Peer Cleaner")

    # =========================
    # 🧠 LIGHT RECOVERY SYSTEM
    # =========================
    def lightweight_recovery():
        while True:
            try:
                if len(p2p_peers) < 3:
                    print("⚠️ Low peers → reconnecting seeds...")
                    connect_seed_nodes()

                if len(blockchain) == 0:
                    print("⚠️ Chain lost → recreating...")
                    create_genesis()

            except Exception as e:
                print("Recovery error:", e)

            time.sleep(15)

    start_thread(lightweight_recovery, "Recovery")

    # =========================
    # ⛏ SMART MINER (OPTIONAL)
    # =========================
    def smart_miner():
        miner_address = os.getenv("MINER_ADDR", "")
        if not miner_address:
            return  # ❗ skip haddii address la'aan

        print("⛏ Smart miner started")

        while True:
            try:
                if len(p2p_peers) < 2:
                    time.sleep(5)
                    continue

                with mempool_lock:
                    if len(pending_transactions) == 0:
                        time.sleep(2)
                        continue

                with app.test_request_context(f"/mine/{miner_address}"):
                    res = mine(miner_address)

                data = res.get_json() if res else None

                if data and "block" in data:
                    print(f"✅ Block mined: {data['block']}")

            except Exception as e:
                print("Miner error:", e)

            time.sleep(1)

    if os.getenv("AUTO_MINE", "false") == "true":
        start_thread(smart_miner, "Smart Miner")

    # =========================
    # 🌍 CONNECT NETWORK
    # =========================
    try:
        load_seed_nodes()
        connect_seed_nodes()
        request_peers()
        request_chain()
        print("🌐 Network connected & synced")
    except Exception as e:
        print("❌ Network error:", e)

    # =========================
    # 🚀 FINAL START
    # =========================
    print("🔥 SomCoin FULLY READY")
    print("🌐 HTTP:", HTTP_PORT)
    print("📡 P2P:", P2P_PORT)

    app.run(
        host="0.0.0.0",
        port=HTTP_PORT,
        use_reloader=False,
        threaded=True
    )
