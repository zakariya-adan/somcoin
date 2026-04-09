# UPDATED 2026
from flask import Flask, request, jsonify, send_from_directory, render_template
import requests
import hashlib
import time
import json
import os
import base64
import socket
import threading
import multiprocessing
from ecdsa import VerifyingKey, SECP256k1

def sha(data):
    return hashlib.sha256(data.encode()).hexdigest()


SERVER_IP = "167.86.117.249"

app = Flask(__name__)

MAX_DIFFICULTY = 4
MIN_DIFFICULTY = 2

def get_new_difficulty(chain):
    if len(chain) < 10:
        return 3

    last_block = chain[-1]
    prev_block = chain[-10]

    time_taken = last_block["timestamp"] - prev_block["timestamp"]
    expected_time = 10 * 60

    difficulty = last_block.get("difficulty", 3)

    if time_taken < expected_time:
        difficulty += 1
    elif time_taken > expected_time:
        difficulty -= 1

    # 🔒 clamp
    if difficulty > MAX_DIFFICULTY:
        difficulty = MAX_DIFFICULTY
    if difficulty < MIN_DIFFICULTY:
        difficulty = MIN_DIFFICULTY

    return difficulty

# ==================================================
# P2P CONFIG (ULTRA PRO GLOBAL VERSION 🚀)
# ==================================================

# 🔥 SCALE UP (GLOBAL NETWORK)
MAX_PEERS = 1000   # ⬅️ muhiim

p2p_peers = set()
peer_ips = set()
banned_ips = set()
peer_id_map = {}

# 📊 PEER INTELLIGENCE (SMART NETWORK)
peer_scores = {}    # ip -> score
peer_failures = {}  # ip -> fail count

# ✅ ONE PORT ONLY (STANDARD)
ALLOWED_PORTS = {9334}

# 🌍 SEED NODES (CORE NETWORK)
SEED_NODES = [
    "167.86.117.249:9334",
    "23.94.66.117:9334",
    "176.177.61.8:9334",

    # 🔥 ADD YOUR VPS NODES HERE
    # "YOUR_VPS_IP:9334",
    # "YOUR_VPS_IP2:9334",
]

# 🔒 MAX LIMIT (ANTI-SPAM)
MAX_CONNECTIONS_PER_IP = 2

# ⛔ BAN RULES
MAX_FAILURES = 5
BAN_TIME = 600  # seconds

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
# 🌍 AUTO DISCOVERY (HTTP BASED 🔥🔥🔥)
# ==================================================
def auto_discover_http():
    while True:
        try:
            # 🔥 seeds ka raadi peers
            for seed in SEED_NODES:
                try:
                    ip, port = seed.split(":")

                    r = requests.get(f"http://{ip}:9443/peers", timeout=3)
                    data = r.json()

                    for p in data.get("peers", []):
                        if p not in p2p_peers and len(p2p_peers) < MAX_PEERS:
                            p2p_peers.add(p)
                            print("🌐 HTTP peer:", p)

                except:
                    continue

            # 🔥 peers ka raadi peers kale
            for peer in list(p2p_peers):
                try:
                    ip, port = peer.split(":")

                    r = requests.get(f"http://{ip}:9443/peers", timeout=3)
                    data = r.json()

                    for p in data.get("peers", []):
                        if p not in p2p_peers and len(p2p_peers) < MAX_PEERS:
                            p2p_peers.add(p)
                            print("🚀 Expanded peer:", p)

                except:
                    continue

        except Exception as e:
            print("HTTP discovery error:", e)

        time.sleep(10)

# ==================================================
# API: GET PEERS
# ==================================================
@app.route("/peers", methods=["GET"])
def get_peers():
    return jsonify({
        "count": len(p2p_peers),
        "peers": list(p2p_peers)
    })



# ==================================================
# NETWORK INFO
# ==================================================
NETWORK_NAME = "SomCoin"
CREATOR = "Zakariya Adan"
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
# STORAGE
# ==================================================

def save_data():

    try:
        tmp = BLOCKCHAIN_FILE + ".tmp"

        with open(tmp, "w") as f:
            json.dump(blockchain, f)

        os.replace(tmp, BLOCKCHAIN_FILE)

    except Exception as e:
        print("Blockchain save error:", e)

    try:
        with open(MEMPOOL_FILE, "w") as f:
            json.dump(pending_transactions, f)
    except:
        pass

    try:
        with open(PEERS_FILE, "w") as f:
            json.dump(list(p2p_peers), f)
    except:
        pass


# ==================================================
# LOAD DATA
# ==================================================
def load_data():

    global blockchain, pending_transactions, p2p_peers

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
                print("Blockchain loaded:", len(blockchain), "blocks")

            else:
                print("Blockchain file empty")

        except Exception as e:

            print("Blockchain load error:", e)

            # ==============================
            # AUTO RECOVERY
            # ==============================
            try:

                with open(BLOCKCHAIN_FILE, "r") as f:
                    raw = f.read()

                cut = raw.rfind('},{"index":')

                if cut != -1:

                    fixed = raw[:cut] + "]"

                    data = json.loads(fixed)

                    if isinstance(data, list) and len(data) > 0:
                        blockchain = data
                        print("Recovered blocks:", len(blockchain))

            except Exception as e2:
                print("Recovery failed:", e2)

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

        except Exception as e:

            print("Mempool load error:", e)
            pending_transactions = []

    # ==============================
    # LOAD PEERS
    # ==============================
    if os.path.exists(PEERS_FILE):
        try:

            with open(PEERS_FILE) as f:

                raw = f.read().strip()

                if raw:
                    p2p_peers = set(json.loads(raw))
                else:
                    p2p_peers = set()

        except Exception as e:

            print("Peers load error:", e)
            p2p_peers = set()

    print("Peers loaded:", len(p2p_peers))


# ==================================================
# ECONOMICS
# ==================================================
TARGET_BLOCK_TIME = 60
difficulty = 4
TX_FEE = 0.01
MAX_TX_PER_BLOCK = 50
MAX_MEMPOOL = 1000

initial_reward = 100
halving_interval = 10000000
MIN_REWARD = 1
max_supply = 21000000

P2P_PORT = int(os.getenv("P2P_PORT", 9334))
HTTP_PORT = int(os.getenv("PORT", 9443))

# ==================================================
# DIFFICULTY ADJUSTMENT
# ==================================================

DIFFICULTY_ADJUSTMENT_INTERVAL = 10
MAX_DIFFICULTY = 4

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

    data = f"{index}{prev_hash}{timestamp}{nonce}{tx_str}".encode()

    return hashlib.sha256(data).hexdigest()

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
# VERIFY SIGNATURE
# ==================================================
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError

def verify_transaction(tx):

    try:
        signature = tx.get("signature")
        public_key_hex = tx.get("public_key")

        if not signature or not public_key_hex:
            return False

        tx_copy = dict(tx)
        tx_copy.pop("signature", None)

        message = json.dumps(tx_copy, sort_keys=True).encode()
        h = hashlib.sha256(message).digest()

        vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)

        return vk.verify(bytes.fromhex(signature), h)

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
# SEND TRANSACTION (SECURE)
# ==================================================
@app.route("/send", methods=["POST"])
def send():

    data = request.json

    sender = data.get("from")
    receiver = data.get("to")
    amount = float(data.get("amount", 0))
    private_key = data.get("private_key")
    public_key = data.get("public_key")

    # hubi fields
    if not sender or not receiver or not private_key or not public_key:
        return jsonify({"error": "missing fields"}), 400

    tx, status = create_transaction(sender, receiver, amount)

    if not tx:
        return jsonify({"error": status}), 400

    # ku dar public key
    tx["public_key"] = public_key

    # sign transaction
    tx["signature"] = sign_transaction(tx, private_key)

    # verify
    if not verify_transaction(tx):
        return jsonify({"error": "Invalid signature"}), 400

    # ku dar mempool
    pending_transactions.append(tx)

    return jsonify({
        "status": "transaction signed & added",
        "tx": tx
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

# ==================================================
# REPLACE CHAIN (FINAL)
# ==================================================
def replace_chain(new_chain):

    global blockchain

    if len(new_chain) <= len(blockchain):
        return

    # validate entire chain
    for i in range(1, len(new_chain)):

        b = new_chain[i]
        prev = new_chain[i-1]

        # check previous hash
        if b["previous_hash"] != prev["hash"]:
            return

        # recalc hash
        h = calculate_hash(
            b["index"],
            b["previous_hash"],
            b["timestamp"],
            b["nonce"],
            b["transactions"]
        )

        if h != b["hash"]:
            return

        # difficulty check
        if not h.startswith("0" * b["difficulty"]):
            return

        # transaction validation
        for tx in b["transactions"]:
            if not verify_tx(tx):
                return

    # ✅ REPLACE
    blockchain = new_chain

    rebuild_utxo()   # 🔥 VERY IMPORTANT

    save_data()

    print("Chain replaced with longer chain:", len(blockchain))


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

# ==================================================
# HANDLE P2P MESSAGE (ULTRA PRO + SAFE + P2P SYNC)
# ==================================================
def handle_msg(msg, conn):

    global blockchain, p2p_peers, pending_transactions

    try:
        # 🔥 SAFE PARSE
        if isinstance(msg, str):
            data = json.loads(msg)
        else:
            data = msg

        msg_type = data.get("type")

        # -----------------------
        # TX
        # -----------------------
        if msg_type == "tx":

            tx = data.get("data")

            if tx and tx not in pending_transactions:

                # 🔒 VERIFY TX
                try:
                    if not verify_tx(tx):
                        return
                except:
                    return

                pending_transactions.append(tx)
                print("💸 TX received")

                p2p_broadcast({
                    "type": "tx",
                    "data": tx
                })

        # -----------------------
        # BLOCK
        # -----------------------
        elif msg_type == "block":

            block = data.get("data")

            if not isinstance(block, dict):
                return

            # ❌ duplicate
            if any(b.get("hash") == block.get("hash") for b in blockchain):
                return

            # ❗ haddii chain ka duwan yahay → sync
            if blockchain and block.get("previous_hash") != blockchain[-1]["hash"]:
                print("⚠️ Out of sync → requesting chain")
                request_chain()
                return

            # 🔒 VALIDATE BLOCK HASH
            tx_str = json.dumps(block["transactions"], sort_keys=True)

            calc_hash = calculate_hash(
                block["index"],
                block["previous_hash"],
                block["timestamp"],
                block["nonce"],
                tx_str
            )

            if calc_hash != block.get("hash"):
                print("❌ Invalid block hash")
                return

            # 🔒 DIFFICULTY CHECK
            if not calc_hash.startswith("0" * block.get("difficulty", 1)):
                print("❌ Invalid difficulty")
                return

            # 🔒 TX VALIDATION
            for tx in block.get("transactions", []):
                if not verify_tx(tx):
                    print("❌ Invalid TX in block")
                    return

            blockchain.append(block)
            update_utxo(block)
            save_data()

            print("✅ Block accepted:", block.get("index"))

            # 🔥 BROADCAST
            p2p_broadcast({
                "type": "block",
                "data": block
            })

        # -----------------------
        # GET CHAIN
        # -----------------------
        elif msg_type == "get_chain":

            conn.sendall((json.dumps({
                "type": "chain",
                "data": blockchain
            }) + "\n").encode())

        # -----------------------
        # CHAIN (🔥 MAIN FIX HERE)
        # -----------------------
        elif msg_type == "chain":

            new_chain = data.get("data")

            if isinstance(new_chain, list):

                # 🔒 VALIDATE FULL CHAIN
                valid = True

                for i in range(1, len(new_chain)):
                    prev = new_chain[i-1]
                    curr = new_chain[i]

                    if curr["previous_hash"] != prev["hash"]:
                        valid = False
                        break

                    tx_str = json.dumps(curr["transactions"], sort_keys=True)

                    calc_hash = calculate_hash(
                        curr["index"],
                        curr["previous_hash"],
                        curr["timestamp"],
                        curr["nonce"],
                        tx_str
                    )

                    if calc_hash != curr["hash"]:
                        valid = False
                        break

                # ✅ REPLACE ONLY IF BETTER
                if valid and len(new_chain) > len(blockchain):

                    print(f"🔄 Better chain found: {len(new_chain)} blocks")

                    blockchain.clear()
                    blockchain.extend(new_chain)

                    rebuild_utxo()
                    save_data()

                    print("✅ Chain replaced (P2P sync)")

        # -----------------------
        # HELLO (SECURE)
        # -----------------------
        elif msg_type == "hello":

            port = data.get("port")
            node_id = data.get("node_id")
            public_key = data.get("public_key")
            signature = data.get("signature")

            # 🔐 VERIFY NODE
            if not verify_node(node_id, public_key, signature):
                print("🚫 Fake node rejected")
                return

            try:
                port = int(port)
            except:
                return

            if not node_id or port not in ALLOWED_PORTS:
                return

            ip = conn.getpeername()[0]

            if ip.startswith("127.") or ip in banned_ips:
                return

            # 🚫 fake identity
            if ip in peer_id_map and peer_id_map[ip] != node_id:
                banned_ips.add(ip)
                print("🚫 FAKE NODE:", ip)
                return

            peer_id_map[ip] = node_id

            peer = f"{ip}:{port}"

            if ip not in peer_ips and len(p2p_peers) < MAX_PEERS:
                p2p_peers.add(peer)
                peer_ips.add(ip)

                clean_peers()
                print("✅ Peer added:", peer)

            # 🔁 reply hello
            conn.sendall((json.dumps({
                "type": "hello",
                "node_id": NODE_ID,
                "port": P2P_PORT,
                "public_key": NODE_PUBLIC_KEY,
                "signature": sign_message(NODE_ID)
            }) + "\n").encode())

        # -----------------------
        # GET PEERS
        # -----------------------
        elif msg_type == "get_peers":

            conn.sendall((json.dumps({
                "type": "peers",
                "data": list(p2p_peers)
            }) + "\n").encode())

        # -----------------------
        # RECEIVE PEERS
        # -----------------------
        elif msg_type == "peers":

            for p in data.get("data", []):

                try:
                    ip, port = p.split(":")
                    port = int(port)

                    if ip in banned_ips:
                        continue

                    if port not in ALLOWED_PORTS:
                        continue

                    if ip in peer_ips:
                        continue

                    if len(p2p_peers) < MAX_PEERS:
                        p2p_peers.add(f"{ip}:{port}")
                        peer_ips.add(ip)

                        clean_peers()
                        print("🌐 Peer discovered:", p)

                except:
                    pass

    except Exception as e:
        print("P2P error:", e)

# ==================================================
# REQUEST PEERS
# ==================================================
def request_peers_socket():

    for peer in list(p2p_peers):

        try:
            ip, port = peer.split(":")
            port = int(port)

            s = socket.socket()
            s.settimeout(5)

            s.connect((ip, port))

            s.sendall((json.dumps({
                "type": "get_peers"
            }) + "\n").encode())

            data = s.recv(100000)

            if data:
                safe_handle(data.decode(), s)

            s.close()

        except:
            pass


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

# =========================
# AUTO PEER SYNC
# =========================
def auto_peer_sync():
    while True:
        try:
            request_peers()
        except:
            pass
        time.sleep(10)

# =========================
# AUTO CONNECT (NEW NODES JOIN 🔥)
# =========================
def auto_connect_new_nodes():
    while True:
        try:
            for peer in list(p2p_peers):
                ip, port = peer.split(":")
                port = int(port)

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

        except:
            pass

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

# =========================
# AUTO CHAIN SYNC
# =========================
def auto_chain_sync():
    while True:
        try:
            request_chain()
        except:
            pass
        time.sleep(15)

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
# P2P SERVER (FINAL PRO - ULTRA STABLE + SECURE)
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

        # 🚫 BLOCK LOCALHOST / INVALID
        if peer_ip.startswith("127.") or peer_ip == "0.0.0.0":
            conn.close()
            continue

        # 🚫 BANNED IPS
        if peer_ip in banned_ips:
            conn.close()
            continue

        def client_thread(c, addr):
            try:
                c.settimeout(10)
                buffer = ""

                while True:
                    data = c.recv(4096)

                    if not data:
                        break

                    # 🔥 SAFE DECODE
                    try:
                        buffer += data.decode(errors="ignore")
                    except:
                        continue

                    # 🔥 MULTI MESSAGE SAFE PARSER
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)

                        if not line.strip():
                            continue

                        # 🔥 ANTI-BROKEN JSON
                        if not line.startswith("{") or not line.endswith("}"):
                            continue

                        # 🔥 ANTI-SPAM (SIZE LIMIT)
                        if len(line) > 100000:
                            continue

                        try:
                            msg = json.loads(line)
                            msg_type = msg.get("type")

                            # 🔒 ALLOW ONLY VALID TYPES
                            if msg_type not in [
                                "hello",
                                "tx",
                                "block",
                                "get_chain",
                                "chain",
                                "get_peers",
                                "peers"
                            ]:
                                continue

                            # 🔥 HANDLE MESSAGE
                            handle_msg(msg, c)

                        except:
                            # 🔕 SILENT IGNORE (NO LOG SPAM)
                            continue

            except:
                # 🔕 IGNORE CONNECTION ERRORS
                pass

            finally:
                try:
                    c.close()
                except:
                    pass

        # 🔥 THREAD PER CONNECTION
        threading.Thread(
            target=client_thread,
            args=(conn, addr),
            daemon=True
        ).start()

# ==================================================
# AUTO CHAIN SYNC
# ==================================================
def sync_chain():

    while True:

        try:
            request_chain()
        except:
            pass

        time.sleep(10)


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
# MINE (ULTRA PRO - FIXED)
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
        # GENESIS
        # =========================================
        if len(blockchain) == 0:
            create_genesis()

        # =========================================
        # MEMPOOL SNAPSHOT
        # =========================================
        with mempool_lock:
            mempool_snapshot = list(pending_transactions)

        # =========================================
        # SELECT TX (fee priority)
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
        # REWARD
        # =========================================
        total_fees = sum(float(tx.get("fee", 0)) for tx in valid_txs)
        reward_amount = block_reward() + total_fees

        coinbase_tx = {
            "sender": "NETWORK",
            "inputs": [],
            "outputs": [{"address": addr, "amount": reward_amount}],
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
            difficulty = get_new_difficulty(blockchain)

        print(f"⛏️ Mining block {index} | diff={difficulty}")

        # =========================================
        # MULTI CPU (FIXED)
        # =========================================
        cpu_count = multiprocessing.cpu_count()

        with multiprocessing.Pool(cpu_count) as pool:

            tasks = [
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

                # 🔥 stop haddii chain change
                with blockchain_lock:
                    if blockchain[-1]["hash"] != prev_hash:
                        print("⚠️ Chain changed → stop mining")
                        return jsonify({"error": "chain changed"})

                for t in tasks:
                    if t.ready():
                        result = t.get()
                        if result:
                            nonce, timestamp, mined_hash = result
                            break

                if nonce is not None:
                    break

                time.sleep(0.01)

        # =========================================
        # BLOCK
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
                print("❌ INVALID BLOCK")
                return jsonify({"error": "invalid block"})

            blockchain.append(block)
            update_utxo(block)

            # REMOVE TX
            with mempool_lock:
                pending_transactions[:] = [
                    tx for tx in pending_transactions if tx not in valid_txs
                ]

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
            print("Broadcast error:", e)

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
        # ✅ FIX muhiim ah (bug kaaga ugu weyn)
        if mining_lock.locked():
            mining_lock.release()

# ==================================================
# GLOBAL STATE
# ==================================================
auto_mining = False
auto_miner_thread = None


# ==================================================
# START AUTO MINER (SAFE VERSION)
# ==================================================
@app.route("/start_auto_mine")
def start_auto_mine():

    global auto_mining, auto_miner_thread

    if auto_mining:
        return jsonify({"status": "already running"})

    auto_mining = True

    def run():
        print("🚀 Auto miner started")
        auto_mine()
        print("🛑 Auto miner exited")

    auto_miner_thread = threading.Thread(target=run)
    auto_miner_thread.daemon = True
    auto_miner_thread.start()

    return jsonify({"status": "started"})


# ==================================================
# STOP AUTO MINER (CLEAN STOP)
# ==================================================
@app.route("/stop_auto_mine")
def stop_auto_mine():

    global auto_mining

    auto_mining = False

    return jsonify({"status": "stopping"})

# ==================================================
# MINER LOAD BALANCER (REAL VPS NETWORK 🔥)
# ==================================================
import random
import requests

# 🌍 REAL VPS NODES (ADD YOUR SERVERS HERE)
MINER_NODES = [
    "http://167.86.117.249:9443",   # VPS 1 (MAIN)
    "http://23.94.66.117:9443",     # VPS 2
    # ku dar VPS kale halkan 👇
    # "http://IP:PORT",
]

# ==================================================
# GET BEST ALIVE NODE (SMART)
# ==================================================
def get_alive_node():

    nodes = MINER_NODES[:]
    random.shuffle(nodes)

    best_node = None
    best_score = -1

    for node in nodes:
        try:
            r = requests.get(f"{node}/api", timeout=3)

            if r.status_code != 200:
                continue

            data = r.json()

            # 📊 SCORE SYSTEM (SMART LOAD BALANCE)
            peers = data.get("peers", 0)
            mempool = data.get("mempool", 0)
            blocks = data.get("blocks", 0)

            # 🔥 formula (optimize mining)
            score = (peers * 3) + (blocks * 2) - (mempool * 4)

            if score > best_score:
                best_score = score
                best_node = node

        except:
            continue

    return best_node


# ==================================================
# MINE PROXY (GLOBAL MINING)
# ==================================================
@app.route("/mine_proxy/<addr>")
def mine_proxy(addr):

    node = get_alive_node()

    if not node:
        return jsonify({
            "error": "❌ no alive nodes",
            "network": "down"
        })

    try:
        r = requests.get(f"{node}/mine/{addr}", timeout=120)

        return jsonify({
            "status": "success",
            "node": node,
            "result": r.json()
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "node": node
        })

# ==================================================
# P2P BROADCAST
# ==================================================
def p2p_broadcast(msg):

    data = (json.dumps(msg) + "\n").encode()

    for peer in list(p2p_peers):
        try:
            host, port = peer.split(":")

            s = socket.socket()
            s.settimeout(3)
            s.connect((host, int(port)))

            s.sendall(data)   # ✅ muhiim

            s.close()

        except Exception as e:
            print("Broadcast fail:", e)


# ==================================================
# HTTP BLOCK RECEIVE (FIXES PROPAGATION)
# ==================================================
@app.route("/receive_block", methods=["POST"])
def receive_block_http():

    global blockchain, pending_transactions

    b = request.json

    # ❗ check duplicate
    if any(block["hash"] == b.get("hash") for block in blockchain):
        return {"status": "duplicate"}

    # ❗ check correct height
    last_block = blockchain[-1]

    if b.get("previous_hash") != last_block["hash"]:
        return {"status": "out_of_sync"}

    if not validate_block(b, blockchain):
        return {"status": "invalid"}

    # ✅ add block
    blockchain.append(b)

    # ✅ remove tx safely
    with mempool_lock:
        pending_transactions[:] = [
            tx for tx in pending_transactions if tx not in b["transactions"]
        ]

    save_data()

    # ✅ broadcast (relay)
    p2p_broadcast({
        "type": "block",
        "data": b
    })

    print(f"🌐 Block received: {b['index']}")

    return {"status": "accepted"}


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
# AUTO MINER (FINAL PRO VERSION)
# ==================================================
auto_mining = False

def auto_mine():

    global auto_mining

    miner_address = "SOM2c6c6c6c5d9412a112ff10f749b40407a986"

    print("⛏️ Auto miner started (stable)...")

    backoff = 1
    last_height = -1   # 🔥 prevent duplicate mining

    while auto_mining:
        try:
            # =========================
            # SAFE READ
            # =========================
            with mempool_lock:
                tx_count = len(pending_transactions)

            with blockchain_lock:
                current_height = blockchain[-1]["index"]
                peer_count = len(p2p_peers)

            print(f"⛏️ Height:{current_height} | tx:{tx_count} | peers:{peer_count}")

            # =========================
            # IDLE MODE
            # =========================
            if tx_count == 0:
                time.sleep(2)
                continue

            # =========================
            # PREVENT RE-MINING SAME BLOCK
            # =========================
            if current_height == last_height:
                time.sleep(0.5)
                continue

            # =========================
            # PREVENT MULTI MINING
            # =========================
            if mining_lock.locked():
                time.sleep(0.5)
                continue

            # =========================
            # MINE BLOCK
            # =========================
            with app.test_request_context(f"/mine/{miner_address}"):
                res = mine(miner_address)

            data = res.get_json() if res else None

            # =========================
            # HANDLE RESULT
            # =========================
            if data and "block" in data:
                print(f"✅ BLOCK {data['block']} mined | reward: {data.get('reward')}")
                last_height = data["block"]
                backoff = 1

            elif data and data.get("status") in ["already mining", "cooldown"]:
                # 🔕 ignore
                pass

            else:
                print("⚠️ Skip:", data)
                backoff = min(backoff + 1, 5)

        except Exception as e:
            print("💥 Miner error:", e)
            backoff = min(backoff * 2, 10)

        time.sleep(backoff)

    print("🛑 Auto miner stopped")


# =========================
# PEER DISCOVERY (FIXED)
# =========================
def auto_discover_peers():
    while True:
        try:
            peers_snapshot = list(p2p_peers)

            # 🔒 limit scan (anti overload)
            sample_peers = random.sample(
                peers_snapshot,
                min(10, len(peers_snapshot))
            )

            for peer in sample_peers:

                try:
                    ip, port = peer.split(":")
                    port = int(port)

                    # 🚫 skip invalid port
                    if port not in ALLOWED_PORTS:
                        continue

                    # 🚫 skip banned
                    if ip in banned_ips:
                        continue

                    s = socket.socket()
                    s.settimeout(5)
                    s.connect((ip, port))

                    # 📡 request peers
                    s.sendall((json.dumps({
                        "type": "get_peers"
                    }) + "\n").encode())

                    buffer = ""

                    while True:
                        chunk = s.recv(4096)

                        if not chunk:
                            break

                        buffer += chunk.decode(errors="ignore")

                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)

                            if not line.strip():
                                continue

                            # 🔒 basic validation
                            if not line.startswith("{") or not line.endswith("}"):
                                continue

                            try:
                                msg = json.loads(line)
                                handle_msg(msg, s)
                            except:
                                continue

                except:
                    continue

                finally:
                    try:
                        s.close()
                    except:
                        pass

            # 💾 SMART SAVE (not every loop)
            if random.randint(1, 5) == 1:
                save_data()

        except Exception as e:
            print("Auto discover error:", e)

        time.sleep(10)


# ================================================
# START NODE (PRO + REAL STABLE VERSION)
# ==================================================
if __name__ == "__main__":

    import os
    import threading
    import time
    import random
    import secrets
    from ecdsa import SigningKey, SECP256k1

    # =========================
    # CONFIG
    # =========================
    HTTP_PORT = int(os.environ.get("PORT", 9443))
    P2P_PORT = int(os.environ.get("P2P_PORT", 9334))

    print("🚀 Starting SomCoin node...")

    # =========================
    # LOAD BLOCKCHAIN
    # =========================
    try:
        load_data()
    except Exception as e:
        print("❌ Load error:", e)

    if not blockchain:
        print("⚠️ Creating genesis block...")
        create_genesis()

    # =========================
    # BUILD UTXO
    # =========================
    try:
        rebuild_utxo()
    except Exception as e:
        print("❌ UTXO rebuild error:", e)

    # =========================
    # THREAD HELPER
    # =========================
    def start_thread(target, name):
        try:
            t = threading.Thread(target=target, daemon=True)
            t.start()
            print(f"✅ {name} started")
        except Exception as e:
            print(f"❌ {name} failed:", e)

    # =========================
    # CORE NETWORK
    # =========================
    start_thread(p2p_server, "P2P Server")
    start_thread(sync_chain, "Chain Sync")

    # =========================
    # NETWORK SYSTEM
    # =========================
    start_thread(auto_discover_peers, "Peer Discovery")
    start_thread(auto_peer_sync, "Peer Sync")
    start_thread(auto_chain_sync, "Chain Sync Auto")
    start_thread(auto_clean_mempool, "Mempool Cleaner")
    start_thread(auto_connect_new_nodes, "Auto Join Network")
    start_thread(auto_discover_http, "HTTP Peer Discovery")
    start_thread(auto_seed_expand, "Seed Expansion")

    # =========================
    # 🔥 REAL TRANSACTION GENERATOR
    # =========================
    def auto_generate_tx():
        print("🔥 Real TX generator started")

        while True:
            try:
                if len(utxo_set) < 2:
                    time.sleep(5)
                    continue

                addrs = list(set(u["address"] for u in utxo_set.values()))

                if len(addrs) < 2:
                    time.sleep(5)
                    continue

                sender = random.choice(addrs)
                receiver = random.choice([a for a in addrs if a != sender])

                amount = round(random.uniform(0.01, 0.2), 4)

                tx, status = create_transaction(sender, receiver, amount)

                if not tx:
                    time.sleep(3)
                    continue

                # 🔐 REAL SIGNATURE
                private_key = secrets.token_hex(32)
                sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
                vk = sk.get_verifying_key()

                tx["public_key"] = vk.to_string().hex()
                tx["signature"] = sign_transaction(tx, private_key)

                # ✅ VERIFY before add
                if verify_tx(tx):
                    with mempool_lock:
                        pending_transactions.append(tx)
                    print("💸 REAL TX added")
                else:
                    print("❌ TX rejected (invalid)")

            except Exception as e:
                print("TX GEN ERROR:", e)

            time.sleep(random.randint(5, 12))

    start_thread(auto_generate_tx, "TX Generator")

    # =========================
    # ⛏ REAL SMART MINER
    # =========================
    def smart_miner():

        miner_address = "SOM2c6c6c6c5d9412a112ff10f749b40407a986"
        print("⛏ Smart miner running (REAL MODE)")

        while True:
            try:
                with mempool_lock:
                    tx_count = len(pending_transactions)

                # ❗ REAL behavior
                if tx_count == 0:
                    print("😴 No transactions...")
                    time.sleep(3)
                    continue

                if mining_lock.locked():
                    time.sleep(1)
                    continue

                with app.test_request_context(f"/mine/{miner_address}"):
                    res = mine(miner_address)

                data = res.get_json() if res else None

                if data and "block" in data:
                    print(f"✅ Block {data['block']} mined | reward: {data.get('reward')}")

                elif data and data.get("status") in ["cooldown", "already mining"]:
                    pass

                else:
                    print("⚠️ Mining skip:", data)

            except Exception as e:
                print("💥 Miner error:", e)

            time.sleep(1)

    start_thread(smart_miner, "Smart Miner")

    # =========================
    # CONNECT NETWORK
    # =========================
    try:
        connect_seed_nodes()
        print("🌐 Connected to network")
    except Exception as e:
        print("❌ Seed error:", e)

    # =========================
    # INITIAL SYNC
    # =========================
    time.sleep(2)
    try:
        request_peers()
        request_chain()
        print("🔄 Sync complete")
    except Exception as e:
        print("❌ Sync error:", e)

    # =========================
    # INFO
    # =========================
    print("🔥 SomCoin READY")
    print("🌐 HTTP:", HTTP_PORT)
    print("📡 P2P:", P2P_PORT)
    print("👥 Peers:", len(p2p_peers))

    # =========================
    # RUN SERVER
    # =========================
    app.run(
        host="0.0.0.0",
        port=HTTP_PORT,
        use_reloader=False,
        threaded=True
    )
