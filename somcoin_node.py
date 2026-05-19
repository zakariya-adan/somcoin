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
import shutil

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

MAX_DIFFICULTY = 5
MIN_DIFFICULTY = 3

# =========================
# DIFFICULTY SYSTEM
# =========================
def get_new_difficulty(chain):
    if len(chain) < 10:
        return MIN_DIFFICULTY

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

# ==================================================
# 🔥 NETWORK DIFFICULTY (BITCOIN STYLE FIXED)
# ==================================================

def dynamic_difficulty():

    with blockchain_lock:

        # =========================
        # EMPTY CHAIN PROTECTION
        # =========================
        if len(blockchain) == 0:
            return MIN_DIFFICULTY

        # =========================
        # REAL CONSENSUS DIFFICULTY
        # =========================
        # ✅ difficulty MUST depend ONLY
        # on blockchain history
        # ❌ NEVER peer count
        # =========================
        difficulty = get_new_difficulty(blockchain)

        # =========================
        # SAFETY LIMITS
        # =========================
        if difficulty < MIN_DIFFICULTY:
            difficulty = MIN_DIFFICULTY

        if difficulty > MAX_DIFFICULTY:
            difficulty = MAX_DIFFICULTY

        return difficulty

# ==================================================
# 🌍 P2P CONFIG (PRO GLOBAL - REAL BITCOIN STYLE 🚀)
# ==================================================

import time
import threading

# =========================
# 🔥 SCALE (SMART SYSTEM)
# =========================
MAX_PEERS = 1000
MAX_ACTIVE_PEERS = 20   # ⚠️ VERY IMPORTANT

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

DNS_SEEDS = [
    "167.86.117.249",
    "23.94.66.117"
]

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


# ==================================================
# 🌐 GOSSIP PEERS (ULTRA FIXED)
# ==================================================
def gossip_peers():

    while True:

        try:

            peers_copy = list(p2p_peers)

            for peer in peers_copy:

                try:

                    if ":" not in peer:
                        continue

                    ip, port = peer.split(":")
                    port = int(port)

                    # 🚫 self skip
                    if (
                        ip == NODE_IP
                        and port == P2P_PORT
                    ):
                        continue

                    # 🚫 banned
                    if is_banned(ip):
                        continue

                    # =========================
                    # 🔥 IMPORTANT FIX
                    # HTTP = 9443
                    # NOT P2P PORT
                    # =========================
                    r = requests.post(
                        f"http://{ip}:9443/peers",
                        json={
                            "peers": peers_copy[:50]
                        },
                        timeout=3
                    )

                    if r.status_code == 200:

                        reward_peer(peer)

                    else:

                        punish_peer(peer)

                except Exception:

                    punish_peer(peer)

        except Exception as e:

            print(
                "Gossip error:",
                e
            )

        time.sleep(10)


# ==================================================
# 🌍 DNS SEED RESOLVER
# ==================================================
def resolve_dns_seeds():

    new_peers = []

    for seed in DNS_SEEDS:

        try:

            ips = socket.gethostbyname_ex(
                seed
            )[2]

            for ip in ips:

                # 🚫 bad ips
                if (
                    ip.startswith("127.")
                    or ip.startswith("0.")
                    or ip == "0.0.0.0"
                ):
                    continue

                peer = f"{ip}:{P2P_PORT}"

                new_peers.append(peer)

        except Exception as e:

            print(
                "DNS seed error:",
                seed,
                e
            )

    return list(set(new_peers))


# ==================================================
# 🔥 ENSURE MINIMUM PEERS
# ==================================================
def ensure_minimum_peers():

    MIN_PEERS = 15

    while True:

        try:

            with peers_lock:

                current = len(p2p_peers)

            # =========================
            # LOW PEERS
            # =========================
            if current < MIN_PEERS:

                print(
                    f"⚠️ Low peers "
                    f"({current}) "
                    f"→ recovering network..."
                )

                # =========================
                # 🔁 RECONNECT SEEDS
                # =========================
                for seed in SEED_NODES:

                    try:

                        if ":" not in seed:
                            continue

                        ip, port = seed.split(":")
                        port = int(port)

                        # 🚫 invalid
                        if (
                            ip.startswith("0.")
                            or ip.startswith("127.")
                            or ip.startswith("255.")
                            or ip == "0.0.0.0"
                        ):
                            continue

                        # =========================
                        # CONNECT P2P
                        # =========================
                        s = socket.socket(
                            socket.AF_INET,
                            socket.SOCK_STREAM
                        )

                        s.settimeout(5)

                        s.connect((ip, port))

                        # =========================
                        # SEND HELLO
                        # =========================
                        hello = {
                            "type": "hello",
                            "public_ip": NODE_IP,
                            "port": P2P_PORT,
                            "node_id": NODE_ID,
                            "public_key": NODE_PUBLIC_KEY,
                            "signature": sign_message(NODE_ID),
                            "version": VERSION,
                            "timestamp": time.time()
                        }

                        s.sendall(
                            (
                                json.dumps(hello)
                                + "\n"
                            ).encode()
                        )

                        # =========================
                        # RECEIVE RESPONSE
                        # =========================
                        try:

                            response = recv_msg(s)

                            if response:

                                safe_handle(
                                    response,
                                    s
                                )

                        except:
                            pass

                        s.close()

                        # =========================
                        # SAVE PEER
                        # =========================
                        with peers_lock:

                            if (
                                len(p2p_peers)
                                < MAX_PEERS
                            ):

                                p2p_peers.add(seed)

                                peer_ips.add(ip)

                                peer_scores[seed] = 10

                                mark_peer_alive(seed)

                        print(
                            "🔁 Reconnected seed:",
                            seed
                        )

                    except Exception as e:

                        print(
                            "Reconnect failed:",
                            seed,
                            e
                        )

                # =========================
                # EXTRA DISCOVERY
                # =========================
                try:
                    bootstrap_peers()
                except:
                    pass

                try:
                    request_peers()
                except:
                    pass

                try:
                    random_bootstrap()
                except:
                    pass

                try:
                    save_peers_safe()
                except:
                    pass

            # =========================
            # STATUS
            # =========================
            print(
                f"👥 Active peers: "
                f"{len(p2p_peers)}"
            )

        except Exception as e:

            print(
                "Ensure peer error:",
                e
            )

        time.sleep(8)

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
# API: GET PEERS
# ==================================================
@app.route("/add_peer/<peer>")
def add_peer(peer):

    try:

        ip, port = peer.split(":")
        port = int(port)

        if add_peer_safe(ip, port):

            return {
                "status": "peer added",
                "peer": f"{ip}:{port}",
                "total": len(p2p_peers)
            }

        return {
            "status": "ignored"
        }

    except Exception as e:

        return {"error": str(e)}


# ==================================================
# NETWORK INFO
# ==================================================
NETWORK_NAME = "SomCoin"
CREATOR = "Zakariya Adan Team"
NETWORK_ID = "SOM_MAINNET_1"
CREATED_YEAR = "2026"

VERSION = "1.0.0"

GENESIS_HASH = "2821c43e2e2c1cdbf39989624dbc33b1b9d4e5c962f9f86814c44e49361f9b5f"

CHECKPOINTS = {
    0: GENESIS_HASH
}

BLOCKCHAIN_FILE = "blockchain.json"
MEMPOOL_FILE = "mempool.json"
PEERS_FILE = "peers.json"

blockchain = []
pending_transactions = []
orphan_blocks = {}

# ==================================================
# UTXO SET
# ==================================================

utxo_set = {}

address_balances = {}

blockchain_lock = threading.RLock()

# ==================================================
# 💾 STORAGE SYSTEM (ULTRA SAFE + PRODUCTION)
# ==================================================

import os
import json
import shutil
import threading

save_lock = threading.Lock()
earn_lock = threading.Lock()

BLOCKCHAIN_FILE = "blockchain.json"
EARN_FILE = "earn.json"

# ==================================================
# 🔥 SAVE DATA
# ==================================================
def save_data():
    global blockchain

    # =========================================
    # SAVE BLOCKCHAIN 🔗
    # =========================================
    try:
        with save_lock:

            tmp_file = BLOCKCHAIN_FILE + ".tmp"
            backup_file = BLOCKCHAIN_FILE + ".bak"

            # 🔥 backup old chain
            if os.path.exists(BLOCKCHAIN_FILE):
                shutil.copy(BLOCKCHAIN_FILE, backup_file)

            # 🔥 write temp file
            with open(tmp_file, "w") as f:

                json.dump(
                    blockchain,
                    f,
                    separators=(",", ":")  # compact JSON
                )

                # 🔥 force write to disk
                f.flush()
                os.fsync(f.fileno())

            # 🔥 atomic replace
            os.replace(tmp_file, BLOCKCHAIN_FILE)

    except Exception as e:
        print("❌ Blockchain save error:", e)

    # =========================================
    # SAVE EARN SYSTEM 💰
    # =========================================
    try:
        with earn_lock:

            data = {
                "balances": balances,
                "referrals": referrals,
                "leaderboard": leaderboard
            }

            tmp_file = EARN_FILE + ".tmp"
            backup_file = EARN_FILE + ".bak"

            # 🔥 backup old earn file
            if os.path.exists(EARN_FILE):
                shutil.copy(EARN_FILE, backup_file)

            # 🔥 write temp file
            with open(tmp_file, "w") as f:

                json.dump(
                    data,
                    f,
                    separators=(",", ":")
                )

                # 🔥 force write to disk
                f.flush()
                os.fsync(f.fileno())

            # 🔥 atomic replace
            os.replace(tmp_file, EARN_FILE)

    except Exception as e:
        print("❌ Earn save error:", e)

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

# ==================================================
# ✅ COMPATIBILITY FIX
# ==================================================
save_peers_safe = save_peers

# ==================================================
# LOAD DATA (ULTRA PRO + DECENTRALIZED 🔥)
# ==================================================
def load_data():

    global blockchain, pending_transactions, p2p_peers
    global balances, referrals, leaderboard

    p2p_peers = set()
    pending_transactions = []

    # ==============================
    # LOAD BLOCKCHAIN
    # ==============================
    if os.path.exists(BLOCKCHAIN_FILE):

        try:

            with open(BLOCKCHAIN_FILE, "r") as f:
                data = json.load(f)

            if isinstance(data, list) and len(data) > 0:

                blockchain = data

                print(
                    "📦 Blockchain loaded:",
                    len(blockchain),
                    "blocks"
                )

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

                    if (
                        isinstance(data, list)
                        and len(data) > 0
                    ):

                        blockchain = data

                        print(
                            "🛠 Recovered blocks:",
                            len(blockchain)
                        )

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

            print(
                "📥 Mempool loaded:",
                len(pending_transactions)
            )

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
                                ip.startswith("127.")
                                or ip.startswith("0.")
                                or ip.startswith("255.")
                                or ip == "0.0.0.0"
                            ):
                                continue

                            if port not in ALLOWED_PORTS:
                                continue

                            cleaned.add(
                                f"{ip}:{port}"
                            )

                        except:
                            continue

                    p2p_peers = cleaned

                else:

                    p2p_peers = set()

        except Exception as e:

            print("❌ Peers load error:", e)

            p2p_peers = set()

    print(
        "🌐 Peers loaded:",
        len(p2p_peers)
    )

    # 🔥 SAVE AFTER CLEAN
    save_peers_safe()

    # ==============================
    # LOAD EARN SYSTEM
    # ==============================
    if os.path.exists(EARN_FILE):

        try:

            with open(EARN_FILE) as f:

                data = json.load(f)

            balances = data.get(
                "balances",
                {}
            )

            referrals = data.get(
                "referrals",
                {}
            )

            leaderboard = data.get(
                "leaderboard",
                {}
            )

            print("💰 Earn system loaded")

        except Exception as e:

            print("❌ Earn load error:", e)

# ==================================================
# ECONOMICS
# ==================================================
TARGET_BLOCK_TIME = 60
difficulty = 4
TX_FEE = 0.01
MAX_TX_PER_BLOCK = 20
MAX_MEMPOOL = 300
MAX_INPUTS = 20

initial_reward = 10
halving_interval = 210000
MIN_REWARD = 1
max_supply = 21000000

P2P_PORT = int(os.getenv("P2P_PORT", 9334))
HTTP_PORT = int(os.getenv("PORT", 9443))

# =========================
# 🔥 BUILD BLOCK TX (BITCOIN STYLE)
# =========================
def build_block_transactions(miner_address):

    txs = sorted(
        pending_transactions,
        key=lambda x: x.get("fee", 0),
        reverse=True
    )

    # 🔥 HARD LIMIT
    txs = txs[:10]

    total_fees = sum(
        tx.get("fee", 0)
        for tx in txs
    )

    coinbase = {
        "sender": "NETWORK",
        "inputs": [],
        "outputs": [{
            "address": miner_address,
            "amount": round(
                block_reward() + total_fees,
                8
            )
        }]
    }

    return [coinbase] + txs

# ==================================================
# GENESIS BLOCK (LOCKED + BITCOIN STYLE 🚀)
# ==================================================
def create_genesis():

    global blockchain
    global utxo_set
    global address_balances

    # =========================
    # LOAD EXISTING BLOCKCHAIN
    # =========================
    if os.path.exists(BLOCKCHAIN_FILE):

        try:

            with open(BLOCKCHAIN_FILE, "r") as f:

                data = json.load(f)

            if isinstance(data, list) and len(data) > 0:

                blockchain = data

                print(
                    f"✅ Existing blockchain loaded "
                    f"| height={len(blockchain)-1}"
                )

                # rebuild state
                if not utxo_set:
                    rebuild_utxo()

                return

        except Exception as e:

            print("⚠️ Blockchain load failed:", e)

    # =========================
    # CREATE GENESIS
    # =========================
    print("🚀 Creating genesis block...")

    genesis_tx = {
        "sender": "NETWORK",
        "inputs": [],
        "outputs": [
            {
                "address": "SOM_GENESIS",
                "amount": 50
            }
        ],
        "message": "SomCoin Genesis Block 2026",
        "timestamp": 1700000000
    }

    genesis = {
        "index": 0,
        "timestamp": 1700000000,
        "transactions": [genesis_tx],
        "nonce": 0,
        "previous_hash": "0" * 64,
        "difficulty": MIN_DIFFICULTY
    }

    # =========================
    # HASH GENESIS
    # =========================
    tx_str = json.dumps(
        genesis["transactions"],
        sort_keys=True
    )

    genesis_hash = calculate_hash(
        genesis["index"],
        genesis["previous_hash"],
        genesis["timestamp"],
        genesis["nonce"],
        tx_str
    )

    genesis["hash"] = genesis_hash

    # =========================
    # SAVE CHAIN
    # =========================
    blockchain = [genesis]

    # =========================
    # BUILD UTXO STATE
    # =========================
    if not utxo_set:
        rebuild_utxo()

    # =========================
    # SAVE TO DISK
    # =========================
    save_data()

    print(
        f"✅ Genesis block created "
        f"| hash={genesis_hash[:32]}..."
    )


# ==================================================
# REBUILD UTXO SET
# ==================================================
def rebuild_utxo():

    global utxo_set
    global address_balances

    # =========================
    # RESET
    # =========================
    utxo_set = {}
    address_balances = {}

    # =========================
    # REBUILD FROM BLOCKCHAIN
    # =========================
    for block in blockchain:

        for tx in block["transactions"]:

            txid = hashlib.sha256(
                json.dumps(tx, sort_keys=True).encode()
            ).hexdigest()

            # =========================
            # REMOVE SPENT INPUTS
            # =========================
            for inp in tx.get("inputs", []):

                key = f'{inp["txid"]}:{inp["index"]}'

                spent = utxo_set.get(key)

                if spent:

                    addr = spent["address"]
                    amt = spent["amount"]

                    # subtract balance
                    address_balances[addr] = round(
                        address_balances.get(addr, 0) - amt,
                        8
                    )

                    del utxo_set[key]

            # =========================
            # ADD OUTPUTS
            # =========================
            for i, out in enumerate(tx.get("outputs", [])):

                amount = round(out.get("amount", 0), 8)

                if amount <= 0:
                    continue

                addr = out["address"]

                key = f"{txid}:{i}"

                utxo_set[key] = {
                    "address": addr,
                    "amount": amount
                }

                # add balance
                address_balances[addr] = round(
                    address_balances.get(addr, 0) + amount,
                    8
                )

    print(
        f"✅ UTXO rebuilt | "
        f"utxos={len(utxo_set)} | "
        f"wallets={len(address_balances)}"
    )


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

        if len(pk_bytes) != 64:
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
# CREATE TRANSACTION (UTXO) ULTRA PRO MAX 🚀
# ==================================================

MAX_INPUTS = 20           # 🔥 hard limit gudaha selection
MAX_TOTAL_INPUTS = 50    # 🔥 network safety limit
DUST_LIMIT = 0.00000001

def create_transaction(sender, receiver, amount, fee=0.001):

    # =========================
    # VALIDATE INPUT
    # =========================
    if not sender or not receiver:
        return None, "Invalid address"

    try:
        amount = float(amount)
    except:
        return None, "Invalid amount format"

    if amount <= 0:
        return None, "Amount must be > 0"

    # =========================
    # CHECK BALANCE
    # =========================
    if balance_with_pending(sender) < amount + fee:
        return None, "Insufficient (including pending)"

    inputs = []
    total = 0

    # =========================
    # COLLECT USER UTXOs
    # =========================
    user_utxos = [
        (key, utxo)
        for key, utxo in utxo_set.items()
        if utxo["address"] == sender
    ]

    if not user_utxos:
        return None, "No UTXOs found"

    # 🔥 SMART SORT (BIG → SMALL = fewer inputs, faster TX)
    user_utxos.sort(key=lambda x: x[1]["amount"], reverse=True)

    # =========================
    # SELECT INPUTS
    # =========================
    for key, utxo in user_utxos:

        # 🔥 HARD LIMIT (performance)
        if len(inputs) >= MAX_INPUTS:
            print("⚠️ MAX_INPUTS reached → partial selection")
            break

        txid, index = key.split(":")
        index = int(index)

        # 🚫 SKIP haddii already mempool ku jiro
        if is_utxo_spent_in_mempool(txid, index):
            continue

        inputs.append({
            "txid": txid,
            "index": index
        })

        total += utxo["amount"]

        # 🎯 STOP haddii lacag ku filan
        if total >= amount + fee:
            break

    # =========================
    # SAFETY CHECK (ANTI-SPAM)
    # =========================
    if len(inputs) > MAX_TOTAL_INPUTS:
        return None, "Too many inputs (network protection)"

    # =========================
    # FINAL CHECK
    # =========================
    if total < amount + fee:
        return None, f"Insufficient balance (collected={round(total,8)})"

    # =========================
    # OUTPUTS
    # =========================
    outputs = []

    # 💸 MAIN PAYMENT
    outputs.append({
        "address": receiver,
        "amount": round(amount, 8)
    })

    # 🔁 CHANGE
    change = round(total - amount - fee, 8)

    # 🔥 DUST PROTECTION (Bitcoin style)
    if change > DUST_LIMIT:
        outputs.append({
            "address": sender,
            "amount": change
        })
    else:
        print("⚠️ Dust ignored:", change)

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

    # =========================
    # DEBUG (VERY IMPORTANT)
    # =========================
    print("==== CREATE TX ====")
    print("Inputs used:", len(inputs))
    print("Total collected:", round(total, 8))
    print("Fee:", fee)
    print("Change:", change)
    print("===================")

    return tx, "OK"

def auto_merge_wallet(address):

    utxos = [
        (key, utxo)
        for key, utxo in utxo_set.items()
        if utxo["address"] == address
    ]

    # haddii UTXO badan yihiin
    if len(utxos) < 20:
        return None

    utxos.sort(key=lambda x: x[1]["amount"])

    inputs = []
    total = 0

    for key, utxo in utxos[:50]:

        txid, index = key.split(":")
        index = int(index)

        if is_utxo_spent_in_mempool(txid, index):
            continue

        inputs.append({
            "txid": txid,
            "index": index
        })

        total += utxo["amount"]

    if total <= 0:
        return None

    return {
        "sender": address,
        "inputs": inputs,
        "outputs": [{
            "address": address,
            "amount": round(total - 0.01, 8)
        }],
        "fee": 0.01,
        "timestamp": time.time()
    }

# ==================================================
# BALANCE (UTXO BASED)
# ==================================================
def balance(addr):
    return round(
        address_balances.get(addr, 0),
        8
    )

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

# =========================
# GET BALANCE (UTXO)
# =========================
@app.route("/get_balance/<address>")
def get_balance(address):

    return jsonify({
        "address": address,
        "balance": balance(address),
        "pending_balance": balance_with_pending(address),
        "utxos": len([
            u for u in utxo_set.values()
            if u["address"] == address
        ])
    })

# ==================================================
# 🚀 SEND TRANSACTION (ULTRA PRO NODE FINAL)
# ==================================================
MIN_TX_FEE = 0.01

@app.route("/send", methods=["POST"])
def send():
    try:
        tx = request.get_json(force=True)

        if not tx:
            return jsonify({"error": "no data"}), 400

        # =========================
        # REQUIRED FIELDS
        # =========================
        required = ["sender", "inputs", "outputs", "signature", "public_key"]

        for field in required:
            if field not in tx:
                return jsonify({
                    "error": "missing field",
                    "field": field
                }), 400

        # =========================
        # TYPE VALIDATION
        # =========================
        if not isinstance(tx["inputs"], list) or len(tx["inputs"]) == 0:
            return jsonify({"error": "invalid inputs"}), 400

        if not isinstance(tx["outputs"], list) or len(tx["outputs"]) == 0:
            return jsonify({"error": "invalid outputs"}), 400

        # =========================
        # INPUT STRUCTURE CHECK
        # =========================
        for inp in tx["inputs"]:
            if "txid" not in inp or "index" not in inp:
                return jsonify({"error": "invalid input format"}), 400

        # =========================
        # OUTPUT STRUCTURE CHECK
        # =========================
        total_output = 0

        for out in tx["outputs"]:
            if "address" not in out or "amount" not in out:
                return jsonify({"error": "invalid output format"}), 400

            try:
                amt = float(out["amount"])
            except:
                return jsonify({"error": "invalid output amount"}), 400

            if amt <= 0:
                return jsonify({"error": "invalid output value"}), 400

            total_output += amt

        # =========================
        # FEE CHECK
        # =========================
        fee = tx.get("fee", 0)

        try:
            fee = float(fee)
        except:
            return jsonify({"error": "invalid fee"}), 400

        if fee < MIN_TX_FEE:
            return jsonify({
                "error": "fee too low",
                "minimum_fee": MIN_TX_FEE
            }), 400

        # =========================
        # SIGNATURE VERIFY 🔐
        # =========================
        if not verify_tx(tx):
            return jsonify({
                "error": "Invalid transaction",
                "reason": "signature or inputs invalid"
            }), 400

        # =========================
        # DOUBLE SPEND CHECK 🔥
        # =========================
        for pending in pending_transactions:
            for inp in tx["inputs"]:
                if any(
                    inp["txid"] == i["txid"] and inp["index"] == i["index"]
                    for i in pending["inputs"]
                ):
                    return jsonify({
                        "error": "double spend detected"
                    }), 400

        # =========================
        # MEMPOOL ADD 🔥
        # =========================
        with mempool_lock:

            if len(pending_transactions) >= MAX_MEMPOOL:
                return jsonify({"error": "mempool full"}), 400

            txid = tx_hash(tx)

            # DUPLICATE CHECK
            if any(tx_hash(t) == txid for t in pending_transactions):
                return jsonify({"error": "duplicate transaction"}), 400

            pending_transactions.append(tx)

        # =========================
        # SUCCESS
        # =========================
        return jsonify({
            "status": "transaction added",
            "txid": txid,
            "fee": fee,
            "recommended_fee": get_recommended_fee(),
            "mempool_size": len(pending_transactions)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "error": "server error",
            "details": str(e)
        }), 500

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
# VERIFY TX (ULTRA SECURE FINAL 🚀)
# ==================================================
def verify_tx(tx, used_inputs=None):

    try:

        # =========================
        # INIT
        # =========================
        if used_inputs is None:
            used_inputs = set()

        # =========================
        # BASIC TYPE
        # =========================
        if not isinstance(tx, dict):
            return False

        # =========================
        # COINBASE TX
        # =========================
        if tx.get("sender") == "NETWORK":

            # no inputs
            if tx.get("inputs"):
                return False

            outputs = tx.get("outputs", [])

            # must have 1 output
            if len(outputs) != 1:
                return False

            out = outputs[0]

            if not isinstance(out, dict):
                return False

            if "address" not in out:
                return False

            if "amount" not in out:
                return False

            amount = float(out["amount"])

            # invalid reward
            if amount <= 0:
                return False

            # anti overmint
            if amount > block_reward() * 2:
                return False

            return True

        # =========================
        # REQUIRED FIELDS
        # =========================
        required = [
            "sender",
            "inputs",
            "outputs",
            "public_key",
            "signature"
        ]

        for field in required:
            if field not in tx:
                return False

        sender = tx["sender"]

        # =========================
        # ADDRESS CHECK
        # =========================
        if not isinstance(sender, str):
            return False

        if not sender.startswith("SOM"):
            return False

        if len(sender) < 10:
            return False

        # =========================
        # INPUTS / OUTPUTS TYPE
        # =========================
        if not isinstance(tx["inputs"], list):
            return False

        if not isinstance(tx["outputs"], list):
            return False

        if len(tx["inputs"]) == 0:
            return False

        if len(tx["outputs"]) == 0:
            return False

        # =========================
        # INPUT LIMIT
        # =========================
        if len(tx["inputs"]) > MAX_TOTAL_INPUTS:
            return False

        # =========================
        # SIGNATURE VERIFY
        # =========================
        try:

            public_key_hex = tx["public_key"]
            signature_hex = tx["signature"]

            public_key = bytes.fromhex(public_key_hex)
            signature = bytes.fromhex(signature_hex)

            # valid key sizes
            if len(public_key) not in (64, 65):
                return False

            # rebuild tx without signature
            tx_copy = dict(tx)
            tx_copy.pop("signature", None)

            message = json.dumps(
                tx_copy,
                sort_keys=True
            ).encode()

            h = hashlib.sha256(message).digest()

            vk = VerifyingKey.from_string(
                public_key,
                curve=SECP256k1
            )

            # verify signature
            if not vk.verify(signature, h):
                return False

            # =========================
            # 🔥 WALLET OWNERSHIP FIX
            # =========================
            derived_address = (
                "SOM" +
                hashlib.sha256(
                    public_key_hex.encode()
                ).hexdigest()[:40]
            )

            if derived_address != sender:
                print("⚠️ Fake sender detected")
                return False

        except Exception as e:

            print(
                "⚠️ Signature verify failed:",
                e
            )

            return False

        # =========================
        # INPUT VALIDATION
        # =========================
        input_sum = 0
        local_inputs = set()

        for inp in tx["inputs"]:

            if not isinstance(inp, dict):
                return False

            if "txid" not in inp:
                return False

            if "index" not in inp:
                return False

            txid = inp["txid"]
            index = inp["index"]

            # type checks
            if not isinstance(txid, str):
                return False

            if not isinstance(index, int):
                return False

            key = f"{txid}:{index}"

            # duplicate input gudaha tx
            if key in local_inputs:
                return False

            local_inputs.add(key)

            # double spend gudaha block
            if key in used_inputs:
                return False

            # UTXO lookup
            utxo = utxo_set.get(key)

            if not utxo:
                return False

            # ownership
            if utxo["address"] != sender:
                return False

            amount = float(
                utxo.get("amount", 0)
            )

            if amount <= 0:
                return False

            input_sum += amount

            used_inputs.add(key)

        # =========================
        # OUTPUT VALIDATION
        # =========================
        output_sum = 0

        for out in tx["outputs"]:

            if not isinstance(out, dict):
                return False

            if "address" not in out:
                return False

            if "amount" not in out:
                return False

            address = out["address"]

            if not isinstance(address, str):
                return False

            if not address.startswith("SOM"):
                return False

            try:
                amount = float(out["amount"])
            except:
                return False

            # invalid amount
            if amount <= 0:
                return False

            # anti dust
            if amount < DUST_LIMIT:
                return False

            output_sum += amount

        # =========================
        # OVERSPEND PROTECTION
        # =========================
        if output_sum > input_sum:
            return False

        # =========================
        # CALCULATE FEE
        # =========================
        fee = round(
            input_sum - output_sum,
            8
        )

        if fee < 0:
            return False

        # anti insane fee
        if fee > input_sum:
            return False

        # =========================
        # FINAL
        # =========================
        return True

    except Exception as e:

        print(
            "❌ TX verify fatal error:",
            e
        )

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
        if not isinstance(chain, list):
            return False

        if len(chain) == 0:
            return False

        # =========================
        # GENESIS CHECK 🔥
        # =========================
        genesis = chain[0]

        # genesis index
        if genesis.get("index") != 0:
            return False

        # genesis previous hash
        if genesis.get("previous_hash") != "0" * 64:
            return False

        # 🔥 REAL GENESIS VERIFY
        if genesis.get("hash") != GENESIS_HASH:
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

                tx_str = json.dumps(
                    b.get("transactions", []),
                    sort_keys=True
                )

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
            difficulty = int(
                b.get("difficulty", 1)
            )

            if not h.startswith(
                "0" * difficulty
            ):
                return False

            # =========================
            # TX VALIDATION 🔥
            # =========================
            used_inputs = set()

            for tx in b.get("transactions", []):

                if not verify_tx(
                    tx,
                    used_inputs
                ):
                    return False

        return True

    except Exception as e:

        print(
            "❌ Chain validation error:",
            e
        )

        return False
# ==================================================
# 🚀 BETTER CHAIN
# (ULTRA PRO MAX 🔥 FIXED)
# ==================================================
def better_chain(new_chain):

    global blockchain

    try:

        # =========================
        # BASIC CHECK
        # =========================
        if not isinstance(new_chain, list):

            print("❌ Reject: not list")

            return False

        if len(new_chain) == 0:

            print("❌ Reject: empty chain")

            return False

        # =========================
        # GENESIS CHECK
        # =========================
        genesis = new_chain[0]

        if genesis.get("index") != 0:

            print("❌ Reject: bad genesis index")

            return False

        if genesis.get("previous_hash") != "0" * 64:

            print("❌ Reject: bad genesis previous hash")

            return False

        # 🔥 REAL GENESIS CHECK
        if genesis.get("hash") != GENESIS_HASH:

            print("❌ Reject: wrong genesis hash")

            return False

        # =========================
        # LOCAL INFO
        # =========================
        local_height = max(0, len(blockchain) - 1)
        new_height = max(0, len(new_chain) - 1)

        local_work = chain_work(blockchain)
        new_work = chain_work(new_chain)

        print(
            f"⚖️ Chain compare | "
            f"local_height={local_height} "
            f"| new_height={new_height} "
            f"| local_work={local_work} "
            f"| new_work={new_work}"
        )

        # =========================
        # FAST SYNC MODE 🔥
        # =========================
        if new_height > 5000:

            print("⚡ Fast sync validation")

            try:

                # 🔥 only verify latest blocks
                recent_blocks = new_chain[-500:]

                # verify chain links
                for i in range(1, len(recent_blocks)):

                    b = recent_blocks[i]
                    prev = recent_blocks[i - 1]

                    if b.get("previous_hash") != prev.get("hash"):

                        print("❌ Fast sync link fail")

                        return False

                print("✅ Fast sync validation passed")

            except Exception as e:

                print(
                    "❌ Fast sync error:",
                    e
                )

                return False

        else:

            # =========================
            # FULL VALIDATION
            # =========================
            if not is_valid_full_chain(new_chain):

                print(
                    "❌ Invalid chain rejected"
                )

                return False

        # =========================
        # WORK CHECK
        # BITCOIN STYLE
        # =========================
        if new_work > local_work:

            print(
                "✅ Stronger chain detected"
            )

            return True

        # =========================
        # HEIGHT FALLBACK
        # =========================
        if (
            new_height > local_height
            and new_work >= local_work * 0.95
        ):

            print(
                "✅ Longer compatible chain"
            )

            return True

        # =========================
        # REJECT
        # =========================
        print("ℹ️ Weaker chain ignored")

        return False

    except Exception as e:

        print(
            "❌ better_chain fatal error:",
            e
        )

        return False


# ==================================================
# 📥 RECEIVE MESSAGE
# ==================================================
def recv_msg(conn):

    try:

        data = b""

        while True:

            chunk = conn.recv(65536)

            if not chunk:
                break

            data += chunk

            # end marker
            if b"\n" in chunk:
                break

        if not data:
            return None

        return data.decode().strip()

    except Exception as e:

        print("recv_msg error:", e)

        return None


# =========================================================
# 🛡 SPAM CHECK
# =========================================================

last_msg_time = {}

def is_spam(ip):

    if ip in banned_ips:
        return True

    now = time.time()

    last = last_msg_time.get(ip, 0)

    # anti spam flood
    if now - last < 0.05:
        return True

    last_msg_time[ip] = now

    return False

# ==================================================
# 🔥 REAL POW HASH
# ==================================================
def calculate_hash(index, previous_hash, timestamp, nonce, tx_str):

    data = (
        f"{index}"
        f"{previous_hash}"
        f"{timestamp}"
        f"{nonce}"
        f"{tx_str}"
    )

    return hashlib.sha256(
        hashlib.sha256(
            data.encode()
        ).digest()
    ).hexdigest()


# =========================================================
# 🔥 TX HASH
# =========================================================

def tx_hash(tx):

    data = json.dumps(
        tx,
        sort_keys=True
    ).encode()

    return hashlib.sha256(
        hashlib.sha256(data).digest()
    ).hexdigest()

# ==================================================
# 🌲 REAL MERKLE TREE
# ==================================================
def merkle_root(transactions):

    if not transactions:
        return hashlib.sha256(b"").hexdigest()

    hashes = [

        tx_hash(tx)

        for tx in transactions
    ]

    while len(hashes) > 1:

        # odd count fix
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])

        new_level = []

        for i in range(0, len(hashes), 2):

            combined = (
                hashes[i] +
                hashes[i + 1]
            )

            h = hashlib.sha256(
                hashlib.sha256(
                    combined.encode()
                ).digest()
            ).hexdigest()

            new_level.append(h)

        hashes = new_level

    return hashes[0]


# =========================
# MINER API (ULTRA PRO 🔥)
# =========================
@app.route("/get_block_template")
def get_block_template():

    try:

        # =========================
        # CHAIN READY
        # =========================
        if not blockchain:

            return jsonify({
                "error": "chain not ready"
            }), 400

        # =========================
        # MINER ADDRESS
        # =========================
        miner_address = request.args.get(
            "address"
        )

        if not miner_address:

            return jsonify({
                "error": "missing miner address"
            }), 400

        # =========================
        # BASIC ADDRESS CHECK
        # =========================
        if not isinstance(miner_address, str):

            return jsonify({
                "error": "invalid address"
            }), 400

        if not miner_address.startswith("SOM"):

            return jsonify({
                "error": "invalid address"
            }), 400

        # =========================
        # LAST BLOCK
        # =========================
        with blockchain_lock:

            if len(blockchain) == 0:

                return jsonify({
                    "error": "empty chain"
                }), 400

            last = blockchain[-1]

            next_index = (
                last["index"] + 1
            )

            prev_hash = (
                last["hash"]
            )

            difficulty = (
                dynamic_difficulty()
            )

        # =========================
        # BUILD TXS
        # =========================
        txs = build_block_transactions(
            miner_address
        )

        # =========================
        # TX CHECK
        # =========================
        if not isinstance(txs, list):

            return jsonify({
                "error": "invalid tx list"
            }), 500

        if len(txs) == 0:

            return jsonify({
                "error": "empty tx list"
            }), 500

        # =========================
        # REAL MERKLE ROOT 🌲
        # =========================
        merkle = merkle_root(txs)

        # =========================
        # TIMESTAMP
        # =========================
        timestamp = int(time.time())

        # =========================
        # BLOCK HEADER
        # =========================
        block_header = (

            f"{next_index}"
            f"{prev_hash}"
            f"{timestamp}"
            f"{merkle}"
        )

        # =========================
        # HEADER HASH
        # =========================
        header_hash = hashlib.sha256(
            hashlib.sha256(
                block_header.encode()
            ).digest()
        ).hexdigest()

        # =========================
        # RESPONSE
        # =========================
        return jsonify({

            "status": "ok",

            "index": next_index,

            "prev_hash": prev_hash,

            "difficulty": difficulty,

            "timestamp": timestamp,

            "merkle_root": merkle,

            "header": block_header,

            "header_hash": header_hash,

            "transactions": txs,

            "tx_count": len(txs),

            "network_time": time.time()
        })

    except Exception as e:

        print(
            "❌ get_block_template error:",
            e
        )

        return jsonify({
            "error": str(e)
        }), 500

# =========================================================
# 🔥 CHAINWORK
# =========================================================

def calculate_chainwork(chain):

    total = 0

    for block in chain:

        try:

            difficulty = int(
                block.get("difficulty", 1)
            )

            total += (2 ** difficulty)

        except:
            continue

    return total

# =========================================================
# 🔥 VALIDATE BLOCK (ULTRA SECURE FINAL)
# =========================================================

def safe_validate_block(block):

    try:

        required = [
            "index",
            "previous_hash",
            "timestamp",
            "nonce",
            "transactions",
            "difficulty",
            "hash"
        ]

        for field in required:

            if field not in block:
                return False

        # =====================================================
        # BLOCK SIZE LIMIT
        # =====================================================

        block_size = len(
            json.dumps(block).encode()
        )

        if block_size > 1_000_000:
            return False

        # =====================================================
        # BASIC TYPES
        # =====================================================

        if not isinstance(block["transactions"], list):
            return False

        if len(block["transactions"]) == 0:
            return False

        if not isinstance(block["index"], int):
            return False

        if not isinstance(block["nonce"], int):
            return False

        # =====================================================
        # NEGATIVE CHECKS
        # =====================================================

        if block["index"] < 0:
            return False

        if block["nonce"] < 0:
            return False

        # =====================================================
        # GENESIS VERIFY
        # =====================================================

        if block["index"] == 0:

            expected = CHECKPOINTS.get(0)

            if expected:

                if block["hash"] != expected:
                    return False

        # =====================================================
        # FUTURE TIME CHECK
        # =====================================================

        if (
            block["timestamp"]
            > time.time() + MAX_FUTURE_TIME
        ):
            return False

        # =====================================================
        # OLD TIME CHECK
        # =====================================================

        if block["timestamp"] < 1700000000:
            return False

        # =====================================================
        # DIFFICULTY VERIFY
        # =====================================================

        if not verify_difficulty(block):
            return False

        # =====================================================
        # HASH VERIFY
        # =====================================================

        tx_str = json.dumps(
            block["transactions"],
            sort_keys=True
        )

        calc_hash = calculate_hash(
            block["index"],
            block["previous_hash"],
            block["timestamp"],
            block["nonce"],
            tx_str
        )

        if calc_hash != block["hash"]:
            return False

        # =====================================================
        # POW VERIFY
        # =====================================================

        difficulty = int(block["difficulty"])

        if difficulty < MIN_DIFFICULTY:
            return False

        if difficulty > MAX_DIFFICULTY:
            return False

        if not block["hash"].startswith(
            "0" * difficulty
        ):
            return False

        # =====================================================
        # HASH LENGTH CHECK
        # =====================================================

        if len(block["hash"]) != 64:
            return False

        # =====================================================
        # COINBASE VERIFY
        # =====================================================

        coinbase = block["transactions"][0]

        # first tx MUST be NETWORK
        if coinbase.get("sender") != "NETWORK":
            return False

        reward = 0

        for out in coinbase.get("outputs", []):

            try:

                amount = float(
                    out.get("amount", 0)
                )

                if amount <= 0:
                    return False

                reward += amount

            except:
                return False

        # =====================================================
        # TOTAL FEES
        # =====================================================

        fees = 0

        for tx in block["transactions"][1:]:

            try:

                fees += float(
                    tx.get("fee", 0)
                )

            except:
                pass

        max_reward = block_reward() + fees

        # anti-overmint
        if reward > max_reward:
            return False

        # =====================================================
        # TX VERIFY
        # =====================================================

        used_inputs = set()

        for tx in block["transactions"]:

            if not verify_tx(tx, used_inputs):
                return False

        # =====================================================
        # BLOCK PASSED
        # =====================================================

        return True

    except Exception as e:

        print("❌ validate block error:", e)

        return False

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
# 🌍 RANDOM BOOTSTRAP (FINAL FIXED)
# ==================================================
def random_bootstrap():

    try:

        # 🚫 no peers
        if not p2p_peers:
            return

        peers = list(p2p_peers)

        # 🔒 limit peers
        peers = peers[:5]

        for peer in peers:

            try:

                if ":" not in peer:
                    continue

                ip, port = peer.split(":")
                port = int(port)

                # 🚫 skip self
                if (
                    ip == NODE_IP
                    and port == P2P_PORT
                ):
                    continue

                # 🚫 banned
                if is_banned(ip):
                    continue

                # =========================
                # CONNECT
                # =========================
                s = socket.socket(
                    socket.AF_INET,
                    socket.SOCK_STREAM
                )

                s.settimeout(3)

                result = s.connect_ex((ip, port))

                # ❌ failed
                if result != 0:
                    s.close()
                    continue

                # =========================
                # SEND HELLO
                # =========================
                hello = {
                    "type": "hello",
                    "public_ip": NODE_IP,
                    "port": P2P_PORT,
                    "node_id": NODE_ID,
                    "public_key": NODE_PUBLIC_KEY,
                    "signature": sign_message(NODE_ID),
                    "version": VERSION,
                    "timestamp": time.time()
                }

                s.sendall(
                    (
                        json.dumps(hello)
                        + "\n"
                    ).encode()
                )

                # ✅ mark alive
                mark_peer_alive(peer)

                s.close()

            except Exception as e:

                punish_peer(peer)

        print(
            f"🌍 Random bootstrap done "
            f"| peers={len(p2p_peers)}"
        )

    except Exception as e:

        print(
            "❌ Random bootstrap error:",
            e
        )

# ==================================================
# 🔥 REQUEST CHAIN FROM PEERS
# ==================================================
def request_chain():

    peers = list(p2p_peers)

    for peer in peers[:5]:

        try:

            ip, port = peer.split(":")

            s = socket.socket()
            s.settimeout(5)

            s.connect((ip, int(port)))

            s.sendall(
                (
                    json.dumps({
                        "type": "get_chain"
                    }) + "\n"
                ).encode()
            )

            s.close()

        except:
            continue

# ==================================================
# 🚀 START BACKGROUND SERVICES
# (BITCOIN STYLE + CLEAN FINAL 🔥)
# ==================================================

def start_background_services():

    print("🚀 Starting background services...")

    services = [

        # 🔄 Peer rotation
        ("rotate_peers", rotate_peers),

        # 🧹 Remove dead peers
        ("clean_dead_peers", clean_dead_peers),

        # ❤️ Keep peers alive
        ("ping_peers", ping_peers),

        # 📡 Share peers
        ("gossip_peers", gossip_peers),

        # 🧠 Ensure minimum peers
        ("ensure_minimum_peers", ensure_minimum_peers),

        # 🌱 Auto expand seeds
        ("auto_seed_expand", auto_seed_expand),

        # ⚖️ Smart seed control
        ("auto_seed_control", auto_seed_control),

        # 🧼 Clean mempool
        ("auto_clean_mempool", auto_clean_mempool),

        # 🔄 Auto blockchain sync
        ("auto_sync", auto_sync),
    ]

    started = set()

    for name, target in services:

        try:

            # 🚫 prevent duplicate thread start
            if name in started:
                continue

            threading.Thread(
                target=target,
                daemon=True,
                name=name
            ).start()

            started.add(name)

            print(f"✅ Started: {name}")

        except Exception as e:

            print(
                f"❌ Failed to start {name}:",
                e
            )

    print("🔥 All background services running")

# ==================================================
# 📩 HANDLE MESSAGE
# (ULTRA PRO MAX FINAL FIXED 🔥)
# ==================================================
def handle_msg(msg, conn=None):

    global pending_transactions
    global orphan_blocks

    try:

        # =====================================
        # SAFE CHECK
        # =====================================
        if not isinstance(msg, dict):
            return

        msg_type = msg.get("type")

        # =====================================
        # HELLO
        # =====================================
        if msg_type == "hello":

            peer_ip = msg.get("public_ip")
            peer_port = msg.get("port", P2P_PORT)

            node_id = msg.get("node_id")
            public_key = msg.get("public_key")
            signature = msg.get("signature")

            # VERSION CHECK
            if msg.get("version") != VERSION:
                return

            # 🚫 reject fake nodes
            if not verify_node(
                node_id,
                public_key,
                signature
            ):

                print(
                    "🚫 Fake node rejected:",
                    peer_ip
                )

                return

            if peer_ip:

                try:
                    peer_port = int(peer_port)

                except:
                    return

                # 🚫 self ignore
                if (
                    peer_ip == NODE_IP
                    and peer_port == P2P_PORT
                ):
                    return

                # 🚫 banned
                if is_banned(peer_ip):
                    return

                # =====================================
                # ADD PEER
                # =====================================
                if add_peer_safe(
                    peer_ip,
                    peer_port
                ):

                    peer_name = (
                        f"{peer_ip}:{peer_port}"
                    )

                    mark_peer_alive(peer_name)

                    reward_peer(peer_name)

                    print(
                        "✅ Verified peer:",
                        peer_name
                    )

                    # =====================================
                    # SEND PEERS BACK
                    # =====================================
                    if conn:

                        try:

                            response = {
                                "type": "peers",
                                "data": list(
                                    p2p_peers
                                )[:50]
                            }

                            conn.sendall(
                                (
                                    json.dumps(response)
                                    + "\n"
                                ).encode()
                            )

                        except Exception as e:

                            print(
                                "❌ Peer response error:",
                                e
                            )

                else:

                    punish_peer(
                        f"{peer_ip}:{peer_port}"
                    )

        # =====================================
        # TX
        # =====================================
        elif msg_type == "tx":

            tx = msg.get("data")

            if not tx:
                return

            # 🔒 verify tx
            if not verify_tx(tx):
                return

            txid = tx_hash(tx)

            # 🚫 duplicate tx
            existing = set()

            for t in pending_transactions:

                try:
                    existing.add(tx_hash(t))
                except:
                    pass

            if txid in existing:
                return

            # 🔒 mempool limit
            if len(pending_transactions) >= MAX_MEMPOOL:
                return

            pending_transactions.append(tx)

            print(
                "📥 TX accepted:",
                txid[:16]
            )

            # 🔥 rebroadcast
            p2p_broadcast({
                "type": "tx",
                "data": tx
            })

        # =====================================
        # BLOCK
        # =====================================
        elif msg_type == "block":

            block = msg.get("data")

            if not block:
                return

            prev_hash = block.get(
                "previous_hash"
            )

            # =====================================
            # ORPHAN BLOCK
            # =====================================
            if (
                len(blockchain) > 0
                and blockchain[-1]["hash"]
                != prev_hash
            ):

                orphan_blocks.setdefault(
                    prev_hash,
                    []
                ).append(block)

                print(
                    "⚠️ Orphan block stored"
                )

                return

            # =====================================
            # PROCESS BLOCK
            # SINGLE SOURCE OF TRUTH
            # =====================================
            if process_new_block(block):

                print(
                    "✅ Block accepted:",
                    block["index"]
                )

                # =====================================
                # CONNECT ORPHANS
                # =====================================
                block_hash = block["hash"]

                if block_hash in orphan_blocks:

                    orphan_list = orphan_blocks.pop(
                        block_hash
                    )

                    for orphan in orphan_list:

                        process_new_block(orphan)

                    print(
                        "✅ Orphan connected"
                    )

            else:

                print(
                    "❌ Failed to add block"
                )

        # =====================================
        # COMPACT BLOCK
        # =====================================
        elif msg_type == "compact_block":

            block = msg.get("data")

            if not block:
                return

            print(
                "📦 Compact block received"
            )

            # reuse block handler
            handle_msg({
                "type": "block",
                "data": block
            }, conn)

        # =====================================
        # GET CHAIN
        # =====================================
        elif msg_type == "get_chain":

            if conn:

                try:

                    response = {
                        "type": "chain",
                        "data": blockchain
                    }

                    conn.sendall(
                        (
                            json.dumps(response)
                            + "\n"
                        ).encode()
                    )

                except Exception as e:

                    print(
                        "❌ Chain send error:",
                        e
                    )

        # =====================================
        # CHAIN
        # =====================================
        elif msg_type == "chain":

            new_chain = msg.get("data")

            if not new_chain:
                return

            maybe_replace_chain(
                new_chain
            )

        # =====================================
        # GET PEERS
        # =====================================
        elif msg_type == "get_peers":

            if conn:

                try:

                    response = {
                        "type": "peers",
                        "data": list(
                            p2p_peers
                        )[:50]
                    }

                    conn.sendall(
                        (
                            json.dumps(response)
                            + "\n"
                        ).encode()
                    )

                except Exception as e:

                    print(
                        "❌ Peer send error:",
                        e
                    )

        # =====================================
        # PEERS
        # =====================================
        elif msg_type == "peers":

            peers = msg.get(
                "data",
                []
            )

            if not isinstance(peers, list):
                return

            for peer in peers[:100]:

                try:

                    if ":" not in peer:
                        continue

                    ip, port = peer.split(":")

                    add_peer_safe(
                        ip,
                        int(port)
                    )

                except:
                    continue

        # =====================================
        # PING
        # =====================================
        elif msg_type == "ping":

            if conn:

                try:

                    conn.sendall(
                        (
                            json.dumps({
                                "type": "pong"
                            })
                            + "\n"
                        ).encode()
                    )

                except:
                    pass

        # =====================================
        # PONG
        # =====================================
        elif msg_type == "pong":

            pass

    except Exception as e:

        print(
            "⚠️ handle_msg error:",
            e
        )

# ==================================================
# P2P SERVER (FINAL PRO - ULTRA STABLE + SECURE 🔥)
# ==================================================
def p2p_server():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind(("0.0.0.0", P2P_PORT))
    s.listen(50)

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
                        if len(line) > 1_000_000:
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
mempool_lock = threading.Lock()

last_mine_time = 0
MINE_COOLDOWN = 1.5   # anti spam

# ==================================================
# 🚀 PROCESS NEW BLOCK
# SINGLE SOURCE OF TRUTH
# ULTRA SECURE FINAL 2026
# ==================================================

def process_new_block(block):

    global blockchain
    global pending_transactions

    try:

        # =========================
        # BASIC CHECK
        # =========================

        if not isinstance(block, dict):
            return False

        block_hash = block.get("hash")

        if not block_hash:
            return False

        # =========================
        # VALIDATE BLOCK
        # =========================

        if not safe_validate_block(block):

            print("❌ Invalid block")

            return False

        with blockchain_lock:

            # =========================
            # EMPTY CHAIN FIX
            # =========================

            if len(blockchain) == 0:

                blockchain.append(block)

                save_data()

                return True

            # =========================
            # DUPLICATE CHECK
            # =========================

            for b in blockchain:

                try:

                    if b["hash"] == block_hash:

                        print("⚠️ Duplicate block")

                        return False

                except:
                    continue

            last_block = blockchain[-1]

            # =========================
            # PREVIOUS HASH CHECK
            # =========================

            if (
                block["previous_hash"]
                != last_block["hash"]
            ):

                print("⚠️ Bad previous hash")

                return False

            # =========================
            # HEIGHT CHECK
            # =========================

            if (
                block["index"]
                != last_block["index"] + 1
            ):

                print("⚠️ Bad height")

                return False

            # =========================
            # TIMESTAMP CHECK
            # =========================

            if (
                block["timestamp"]
                <= last_block["timestamp"]
            ):

                print("⚠️ Bad timestamp")

                return False

            # =========================
            # ADD BLOCK
            # =========================

            blockchain.append(block)

        # =========================
        # UPDATE UTXO
        # =========================

        try:

            update_utxo(block)

        except Exception as e:

            print(
                "⚠️ update_utxo failed:",
                e
            )

            rebuild_utxo()

        # =========================
        # CLEAN MEMPOOL
        # =========================

        confirmed = set()

        for tx in block["transactions"]:

            try:

                confirmed.add(
                    tx_hash(tx)
                )

            except:
                pass

        with mempool_lock:

            cleaned = []

            for tx in pending_transactions:

                try:

                    if (
                        tx_hash(tx)
                        not in confirmed
                    ):

                        cleaned.append(tx)

                except:
                    continue

            pending_transactions[:] = cleaned

        # =========================
        # RECENT CACHE
        # =========================

        try:

            add_recent_block(block_hash)

        except:
            pass

        # =========================
        # SAVE
        # =========================

        try:

            save_data()

        except Exception as e:

            print(
                "❌ save error:",
                e
            )

        # =========================
        # BROADCAST
        # =========================

        try:

            p2p_broadcast({

                "type": "compact_block",

                "data": block
            })

        except Exception as e:

            print(
                "⚠️ broadcast error:",
                e
            )

        # =========================
        # SUCCESS LOG
        # =========================

        print(
            f"🔥 BLOCK ACCEPTED "
            f"| height={block['index']} "
            f"| hash={block_hash[:20]}"
        )

        return True

    except Exception as e:

        print(
            "❌ Process block error:",
            e
        )

        return False

# =========================================================
# 🚀 SUBMIT BLOCK
# =========================================================

@app.route("/submit_block", methods=["POST"])
def submit_block():

    try:

        block = request.get_json()

        # =========================
        # VALIDATE INPUT
        # =========================
        if not isinstance(block, dict):

            return jsonify({
                "error": "invalid block"
            })

        # =========================
        # SINGLE SOURCE OF TRUTH
        # =========================
        success = process_new_block(block)

        if not success:

            return jsonify({
                "error": "block rejected"
            })

        # =========================
        # SUCCESS
        # =========================
        return jsonify({

            "status": "accepted",

            "height": block["index"],

            "hash": block["hash"]
        })

    except Exception as e:

        print(
            "❌ submit block error:",
            e
        )

        return jsonify({
            "error": str(e)
        })

# =========================================================
# 🚀 HEALTH
# =========================================================

@app.route("/health")
def health():

    try:

        return jsonify({

            "status": "ok",

            "blocks": len(blockchain),

            "peers": len(p2p_peers),

            "mempool": len(pending_transactions),

            "difficulty": dynamic_difficulty(),

            "network": "SomCoin"
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        })


@app.route("/headers")
def headers():

    try:

        limit = request.args.get(
            "limit",
            default=2000,
            type=int
        )

        start = request.args.get(
            "start",
            default=0,
            type=int
        )

        result = []

        end = min(
            start + limit,
            len(blockchain)
        )

        for b in blockchain[start:end]:

            result.append({

                "index": b["index"],

                "hash": b["hash"],

                "previous_hash":
                b["previous_hash"],

                "timestamp":
                b["timestamp"],

                "difficulty":
                b.get("difficulty", 1)

            })

        return jsonify({

            "headers": result,

            "height": len(blockchain)-1

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


@app.route("/block_by_hash/<block_hash>")
def block_by_hash(block_hash):

    for b in blockchain:

        if b["hash"] == block_hash:

            return jsonify({
                "block": b
            })

    return jsonify({
        "error": "not found"
    }), 404


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
# 🚀 P2P BROADCAST
# (ULTRA SAFE + BITCOIN STYLE 🔥)
# ==================================================
import random

recent_messages = set()

def p2p_broadcast(msg):

    global recent_messages

    try:

        # =========================================
        # SAFE MESSAGE ID
        # =========================================
        msg_id = hashlib.sha256(
            json.dumps(
                msg,
                sort_keys=True
            ).encode()
        ).hexdigest()

        # 🚫 prevent rebroadcast spam
        if msg_id in recent_messages:
            return

        recent_messages.add(msg_id)

        # 🔒 memory protection
        if len(recent_messages) > 5000:
            recent_messages.clear()

    except Exception as e:

        print(
            "Broadcast hash error:",
            e
        )

        return

    # =========================================
    # BUILD DATA
    # =========================================
    try:

        data = (
            json.dumps(msg)
            + "\n"
        ).encode()

    except Exception as e:

        print(
            "Broadcast encode error:",
            e
        )

        return

    # =========================================
    # BEST PEERS
    # =========================================
    try:

        best = get_best_peers(
            MAX_ACTIVE_BROADCAST // 2
        )

    except:

        best = []

    # =========================================
    # RANDOM PEERS (SAFE FIX 🔥)
    # =========================================
    peer_list = list(p2p_peers)

    if peer_list:

        try:

            random_peers = random.sample(
                peer_list,
                min(
                    MAX_ACTIVE_BROADCAST // 2,
                    len(peer_list)
                )
            )

        except:

            random_peers = []

    else:

        random_peers = []

    # =========================================
    # FINAL PEERS
    # =========================================
    peers = list(
        set(best + random_peers)
    )

    # =========================================
    # NO PEERS
    # =========================================
    if not peers:
        return

    # =========================================
    # BROADCAST
    # =========================================
    for peer in peers:

        try:

            if ":" not in peer:
                continue

            ip, port = peer.split(":")
            port = int(port)

            # 🚫 banned
            if is_banned(ip):
                continue

            # 🚫 self skip
            if (
                ip == NODE_IP
                and port == P2P_PORT
            ):
                continue

            # =====================================
            # CONNECT
            # =====================================
            s = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            s.settimeout(2)

            result = s.connect_ex(
                (ip, port)
            )

            # ❌ failed
            if result != 0:

                s.close()

                punish_peer(peer)

                continue

            # =====================================
            # SEND
            # =====================================
            s.sendall(data)

            s.close()

            # ✅ reward
            reward_peer(peer)

        except Exception:

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
# 🌐 GET PEERS API
# ==================================================
@app.route("/peers", methods=["GET", "POST"])
def peers_api():

    global p2p_peers

    # =========================
    # POST = RECEIVE PEERS
    # =========================
    if request.method == "POST":

        try:

            data = request.get_json(force=True)

            new_peers = data.get("peers", [])

            added = 0

            for peer in new_peers:

                try:

                    ip, port = peer.split(":")
                    port = int(port)

                    if add_peer_safe(ip, port):
                        added += 1

                except:
                    continue

            return jsonify({
                "status": "ok",
                "added": added,
                "total": len(p2p_peers)
            })

        except Exception as e:

            return jsonify({
                "error": str(e)
            })

    # =========================
    # GET = SHARE PEERS
    # =========================
    return jsonify({
        "peers": list(p2p_peers)[:100]
    })

# ==================================================
# ⛏ HASHRATE
# ==================================================
def calculate_hashrate():

    try:

        if len(blockchain) < 2:
            return 0

        latest = blockchain[-1]

        difficulty = latest.get("difficulty", 1)

        return round((2 ** difficulty) / TARGET_BLOCK_TIME, 2)

    except:
        return 0

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

# ==================================================
# GET JOB (STRATUM READY + SECURE + PRO 🚀)
# ==================================================

@app.route("/get_job")
def get_job():

    try:

        # =========================================
        # GET TEMPLATE
        # =========================================
        template = requests.get(
            f"http://127.0.0.1:9443/get_block_template?address={ADDRESS}",
            timeout=5
        ).json()

        # =========================================
        # TEMPLATE CHECK
        # =========================================
        if not isinstance(template, dict):

            return jsonify({
                "error": "invalid template"
            })

        if "error" in template:

            return jsonify({
                "error": template["error"]
            })

        # =========================================
        # REQUIRED FIELDS
        # =========================================
        required = [

            "index",
            "prev_hash",
            "timestamp",
            "difficulty",
            "merkle_root"
        ]

        for field in required:

            if field not in template:

                return jsonify({
                    "error": f"missing {field}"
                })

        # =========================================
        # BUILD HEADER
        # =========================================
        global block_header

        block_header = (

            str(template["index"]) +

            str(template["prev_hash"]) +

            str(template["timestamp"]) +

            str(template["merkle_root"])
        )

        # =========================================
        # HEADER HASH
        # =========================================
        header_hash = hashlib.sha256(
            block_header.encode()
        ).hexdigest()

        # =========================================
        # JOB ID
        # =========================================
        job_id = hashlib.sha256(

            f"{block_header}{time.time()}".encode()

        ).hexdigest()[:16]

        # =========================================
        # STORE ACTIVE JOB
        # =========================================
        global current_jobs

        current_jobs[job_id] = {

            "created": time.time(),

            "template": template,

            "header": block_header,

            "header_hash": header_hash
        }

        # =========================================
        # CLEAN OLD JOBS
        # =========================================
        now = time.time()

        expired = []

        for jid, data in current_jobs.items():

            if now - data["created"] > 120:
                expired.append(jid)

        for jid in expired:
            del current_jobs[jid]

        # =========================================
        # RESPONSE
        # =========================================
        return jsonify({

            "status": "ok",

            "job_id": job_id,

            "index": template["index"],

            "difficulty": template["difficulty"],

            "prev_hash": template["prev_hash"],

            "merkle_root": template["merkle_root"],

            "timestamp": template["timestamp"],

            "header": block_header,

            "header_hash": header_hash
        })

    except requests.exceptions.Timeout:

        return jsonify({
            "error": "node timeout"
        })

    except requests.exceptions.ConnectionError:

        return jsonify({
            "error": "node offline"
        })

    except Exception as e:

        print("❌ get_job error:", e)

        return jsonify({
            "error": str(e)
        })

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
# 🚀 GET CHAIN
# (FAST + FULL SYNC SUPPORT)
# ==================================================
@app.route("/chain")
def get_chain():

    try:

        limit = request.args.get(
            "limit",
            type=int
        )

        # default = last 500 blocks only
        if not limit:
            limit = 500

        MAX_LIMIT = 2000

        if limit > MAX_LIMIT:
            limit = MAX_LIMIT

        data = blockchain[-limit:]

        return jsonify({
            "chain": data,
            "count": len(data),
            "height": len(blockchain) - 1
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

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
        "difficulty": dynamic_difficulty(),
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
# RICH LIST API
# ==================================================
@app.route("/richlist")
def richlist_api():

    try:

        rich = []

        # =========================
        # BUILD FROM REAL BALANCES
        # =========================
        for addr, bal in address_balances.items():

            try:
                bal = round(float(bal), 8)
            except:
                continue

            # skip empty wallets
            if bal <= 0:
                continue

            # count utxos
            utxo_count = sum(
                1 for u in utxo_set.values()
                if u["address"] == addr
            )

            rich.append({
                "address": addr,
                "balance": bal,
                "utxos": utxo_count
            })

        # =========================
        # SORT BIGGEST HOLDERS
        # =========================
        rich.sort(
            key=lambda x: x["balance"],
            reverse=True
        )

        # =========================
        # FINAL
        # =========================
        final = []

        for i, r in enumerate(rich[:100]):

            final.append({
                "rank": i + 1,
                "address": r["address"],
                "balance": r["balance"],
                "utxos": r["utxos"]
            })

        return jsonify({
            "total_wallets": len(address_balances),
            "richlist": final
        })

    except Exception as e:

        import traceback
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

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


# ==================================================
# 🌱 SEED NODES (REAL NETWORK BASE)
# ==================================================

def load_seed_nodes():
    for seed in SEED_NODES:
        if seed not in p2p_peers:
            p2p_peers.add(seed)
            peer_scores[seed] = 10  # 🔥 trusted

# ==================================================
# 🌍 AUTO BLOCKCHAIN SYNC
# ULTRA PRO MAX (FIXED + FAST + SAFE 🚀)
# ==================================================
def auto_sync():

    global blockchain

    while True:

        try:

            # =========================
            # LOCAL STATE
            # =========================
            local_height = len(blockchain) - 1
            local_work = chain_work(blockchain)

            # =========================
            # BEST PEERS ONLY
            # =========================
            peers = get_best_peers(10)

            if not peers:
                time.sleep(30)
                continue

            # =========================
            # LOOP PEERS
            # =========================
            for peer in peers:

                try:

                    ip, port = peer.split(":")
                    port = int(port)

                    # 🚫 skip self
                    if ip == NODE_IP:
                        continue

                    # =========================
                    # GET PEER INFO
                    # =========================
                    r = requests.get(
                        f"http://{ip}:9443/api",
                        timeout=5
                    )

                    if r.status_code != 200:
                        punish_peer(peer)
                        continue

                    info = r.json()

                    peer_height = int(
                        info.get("blocks", 0)
                    ) - 1

                    peer_diff = int(
                        info.get("difficulty", 1)
                    )

                    # =========================
                    # PEER NOT AHEAD
                    # =========================
                    if peer_height <= local_height:
                        reward_peer(peer)
                        continue

                    print(
                        f"🌍 Sync candidate {peer} "
                        f"| local={local_height} "
                        f"| peer={peer_height} "
                        f"| diff={peer_diff}"
                    )

                    # =========================
                    # DOWNLOAD CHAIN
                    # =========================
                    r = requests.get(
                        f"http://{ip}:9443/chain",
                        timeout=20
                    )

                    if r.status_code != 200:
                        punish_peer(peer)
                        continue

                    # =========================
                    # SAFE JSON
                    # =========================
                    try:
                        data = r.json()
                    except:
                        punish_peer(peer)
                        continue

                    # =========================
                    # NEW FORMAT SUPPORT
                    # =========================
                    if isinstance(data, dict):

                        new_chain = data.get(
                            "chain",
                            []
                        )

                    elif isinstance(data, list):

                        # backward compatibility
                        new_chain = data

                    else:
                        punish_peer(peer)
                        continue

                    # =========================
                    # VALIDATE FORMAT
                    # =========================
                    if not isinstance(new_chain, list):
                        punish_peer(peer)
                        continue

                    if len(new_chain) == 0:
                        punish_peer(peer)
                        continue

                    # =========================
                    # QUICK HEIGHT CHECK
                    # =========================
                    new_height = len(new_chain) - 1

                    if new_height <= local_height:
                        continue

                    # =========================
                    # QUICK WORK CHECK
                    # =========================
                    new_work = chain_work(new_chain)

                    if new_work <= local_work:
                        print(
                            f"ℹ️ Weak chain ignored "
                            f"| peer={peer}"
                        )

                        continue

                    # =========================
                    # VALIDATE CHAIN
                    # =========================
                    if not better_chain(new_chain):

                        print(
                            f"❌ Invalid chain "
                            f"from {peer}"
                        )

                        punish_peer(peer)
                        continue

                    # =========================
                    # REPLACE CHAIN
                    # =========================
                    print(
                        f"✅ Syncing from {peer} "
                        f"| new_height={new_height}"
                    )

                    success = replace_chain(
                        new_chain
                    )

                    if success:

                        reward_peer(peer)

                        rebuild_utxo()

                        save_data()

                        print(
                            f"🔥 Sync complete "
                            f"| height={len(blockchain)-1}"
                        )

                        break

                    else:

                        punish_peer(peer)

                except requests.exceptions.Timeout:

                    print(
                        f"⏱ Sync timeout: {peer}"
                    )

                    punish_peer(peer)

                except requests.exceptions.ConnectionError:

                    print(
                        f"❌ Dead peer: {peer}"
                    )

                    punish_peer(peer)

                except Exception as e:

                    print(
                        f"⚠️ Peer sync error "
                        f"{peer}:",
                        e
                    )

                    punish_peer(peer)

        except Exception as e:

            print(
                "❌ Auto sync fatal error:",
                e
            )

        # =========================
        # LOOP DELAY
        # =========================
        time.sleep(15)

# =========================
# 🧱 ORPHAN SYSTEM
# =========================
orphan_blocks = {}

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

# ==================================================
# 🌍 REQUEST PEERS
# ==================================================
def request_peers():

    for peer in list(p2p_peers):

        try:

            if ":" not in peer:
                continue

            ip, port = peer.split(":")
            port = int(port)

            s = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            s.settimeout(5)

            s.connect((ip, port))

            s.sendall(
                (
                    json.dumps({
                        "type": "get_peers"
                    }) + "\n"
                ).encode()
            )

            s.close()

        except:
            continue


# ==================================================
# 🌱 BOOTSTRAP PEERS
# ==================================================
def bootstrap_peers():

    while True:

        try:

            for seed in SEED_NODES:

                try:

                    if ":" not in seed:
                        continue

                    ip, port = seed.split(":")
                    port = int(port)

                    # skip self
                    if (
                        ip == NODE_IP
                        and port == P2P_PORT
                    ):
                        continue

                    s = socket.socket(
                        socket.AF_INET,
                        socket.SOCK_STREAM
                    )

                    s.settimeout(5)

                    result = s.connect_ex(
                        (ip, port)
                    )

                    if result != 0:
                        s.close()
                        continue

                    hello = {

                        "type": "hello",

                        "public_ip": NODE_IP,

                        "port": P2P_PORT,

                        "node_id": NODE_ID,

                        "public_key": NODE_PUBLIC_KEY,

                        "signature": sign_message(
                            NODE_ID
                        ),

                        "version": VERSION,

                        "timestamp": time.time()
                    }

                    s.sendall(
                        (
                            json.dumps(hello)
                            + "\n"
                        ).encode()
                    )

                    s.close()

                    add_peer_safe(ip, port)

                except:
                    continue

        except Exception as e:

            print(
                "Bootstrap error:",
                e
            )

        time.sleep(30)

# ==================================================
# 🧠 SMART PEER DISCOVERY
# ==================================================
def smart_discovery():

    while True:

        try:

            # request peers
            request_peers()

            # bootstrap seeds
            for seed in SEED_NODES:

                try:

                    if ":" not in seed:
                        continue

                    ip, port = seed.split(":")
                    port = int(port)

                    add_peer_safe(ip, port)

                except:
                    continue

            print(
                "✅ Smart discovery updated"
            )

        except Exception as e:

            print(
                "❌ Smart discovery error:",
                e
            )

        time.sleep(60)

# ================================================
# 🚀 START NODE (BITCOIN STYLE CLEAN FINAL)
# ================================================
if __name__ == "__main__":

    import os
    import threading
    import time

    # =========================
    # CONFIG
    # =========================
    HTTP_PORT = int(
        os.environ.get("PORT", 9443)
    )

    P2P_PORT = int(
        os.environ.get("P2P_PORT", 9334)
    )

    print("🚀 Starting SomCoin Node...")

    # =========================
    # SAFE THREAD STARTER
    # =========================
    def start_thread(target, name):

        def wrapper():

            while True:

                try:
                    target()

                except Exception as e:

                    print(
                        f"💥 {name} crashed:",
                        e
                    )

                    time.sleep(3)

        t = threading.Thread(
            target=wrapper,
            daemon=True
        )

        t.start()

        print(f"✅ {name} started")

    # =========================
    # LOAD BLOCKCHAIN
    # =========================
    try:

        load_data()

        print(
            f"✅ Blockchain loaded "
            f"| blocks={len(blockchain)-1}"
        )

    except Exception as e:

        print(
            "❌ Load error:",
            e
        )

    # =========================
    # CREATE GENESIS
    # =========================
    if len(blockchain) == 0:

        print(
            "⚠️ No blockchain found "
            "→ creating genesis..."
        )

        create_genesis()

    # =========================
    # LOAD SEEDS
    # =========================
    try:

        load_seed_nodes()

        print(
            "✅ Seed nodes loaded"
        )

    except Exception as e:

        print(
            "❌ Seed load error:",
            e
        )

    # =========================
    # REQUEST PEERS
    # =========================
    try:

        request_peers()

        print(
            "✅ Requested peer data"
        )

    except Exception as e:

        print(
            "❌ Request error:",
            e
        )

    # =========================
    # REBUILD UTXO
    # =========================
    try:

        rebuild_utxo()

        print(
            f"✅ UTXO rebuilt "
            f"| utxos={len(utxo_set)}"
        )

    except Exception as e:

        print(
            "❌ UTXO error:",
            e
        )

    # =========================
    # 🌐 CORE NETWORK
    # =========================
    start_thread(
        p2p_server,
        "P2P Server"
    )

    start_thread(
        bootstrap_peers,
        "Peer Bootstrap"
    )

    start_thread(
        smart_discovery,
        "Peer Discovery"
    )

    start_thread(
        ensure_minimum_peers,
        "Peer Recovery"
    )

    start_thread(
        auto_sync,
        "Auto Sync"
    )

    start_thread(
        ping_peers,
        "Peer KeepAlive"
    )

    # =========================
    # CLEANERS
    # =========================
    start_thread(
        auto_clean_mempool,
        "Mempool Cleaner"
    )

    start_thread(
        clean_peer_ips,
        "Peer IP Cleaner"
    )

    start_thread(
        clean_dead_peers,
        "Dead Peer Cleaner"
    )

    # =========================
    # ORPHAN FIX
    # =========================
    start_thread(
        auto_resolve_orphans,
        "Orphan Resolver"
    )

    # =========================
    # FINAL STATUS
    # =========================
    print("🔥 SomCoin NODE READY")

    print(
        f"🌐 HTTP PORT: {HTTP_PORT}"
    )

    print(
        f"📡 P2P PORT: {P2P_PORT}"
    )

    print(
        f"⛓ BLOCKS: "
        f"{len(blockchain)-1}"
    )

    print(
        f"👥 PEERS: "
        f"{len(p2p_peers)}"
    )

    print(
        f"💰 UTXOS: "
        f"{len(utxo_set)}"
    )

    # =========================
    # START API
    # =========================
    app.run(
        host="0.0.0.0",
        port=HTTP_PORT,
        use_reloader=False,
        threaded=True
    )
