# =========================================================
# 🚀 ULTRA PRO MAX FINAL MINER (2026)
# =========================================================

import requests
import hashlib
import time
import json
import gc
import os
import signal
import threading

# =========================================================
# 🚀 PERFORMANCE
# =========================================================

gc.disable()

session = requests.Session()

# =========================================================
# ⚙️ CONFIG
# =========================================================

NODE_URL = "http://127.0.0.1:9443"

ADDRESS = "SOMGjFnfFWcFTTc7HsftBXdQP4wSDgYyE"

REQUEST_TIMEOUT = 120

HASH_UPDATE_INTERVAL = 5_000_000

TEMPLATE_REFRESH_NONCE = 5_000_000

AUTO_RECONNECT_DELAY = 3

MAX_NONCE = 2**64

# =========================================================
# 🚀 GLOBALS
# =========================================================

running = True

current_hashrate = 0

shares = 0

# =========================================================
# 🔥 DOUBLE SHA256
# =========================================================

def double_sha256(data):

    return hashlib.sha256(
        hashlib.sha256(
            data.encode()
        ).digest()
    ).hexdigest()


# =========================================================
# 📦 GET TEMPLATE
# =========================================================

def get_template():

    r = session.get(
        f"{NODE_URL}/get_block_template?address={ADDRESS}",
        timeout=REQUEST_TIMEOUT
    )

    return r.json()


# =========================================================
# 🚀 SEND HASHRATE
# =========================================================

def send_hashrate(hr, shares_count):

    try:

        session.post(
            "https://somcoin.online/submit_miner",

            json={
                "address": ADDRESS,
                "hashrate": hr,
                "shares": shares_count
            },

            timeout=5
        )

    except:
        pass


# =========================================================
# 🚀 SUBMIT BLOCK
# =========================================================

def submit_block(block):

    try:

        r = session.post(

            f"{NODE_URL}/submit_block",

            json=block,

            timeout=REQUEST_TIMEOUT
        )

        try:

            return r.json()

        except:

            return {
                "success": False,
                "error": r.text
            }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# =========================================================
# ❤️ HEALTH CHECK
# =========================================================

def health_check():

    while running:

        try:

            r = session.get(
                f"{NODE_URL}/health",
                timeout=10
            )

            if r.status_code == 200:

                data = r.json()

                print(
                    f"\n💚 NODE OK "
                    f"| height={data.get('height')} "
                    f"| peers={data.get('peers')}"
                )

        except Exception as e:

            print(
                "\n⚠️ Health check failed:",
                e
            )

        time.sleep(60)


# =========================================================
# 🚀 SIGNAL HANDLER
# =========================================================

def signal_handler(sig, frame):

    global running

    running = False

    print("\n🛑 Miner shutting down...")

    os._exit(0)


signal.signal(
    signal.SIGINT,
    signal_handler
)

signal.signal(
    signal.SIGTERM,
    signal_handler
)

# =========================================================
# ⛏ ULTRA STABLE  STYLE MINER
# =========================================================

def mine():

    global current_hashrate
    global shares

    print("🚀 SomCoin Decentralized Miner")
    print("🌐 Node:", NODE_URL)
    print("💰 Address:", ADDRESS)

    threading.Thread(
        target=health_check,
        daemon=True
    ).start()

    while running:

        try:

            # =============================================
            # GET TEMPLATE
            # =============================================

            tpl = get_template()

            if (
                not tpl or
                "error" in tpl
            ):

                print("❌ Template error")

                time.sleep(2)

                continue

            # =============================================
            # BLOCK DATA
            # =============================================

            index = tpl["index"]

            prev_hash = tpl["prev_hash"]

            difficulty = int(
                tpl["difficulty"]
            )

            timestamp = tpl["timestamp"]

            txs = tpl["transactions"]

            tx_str = json.dumps(
                txs,
                sort_keys=True,
                separators=(",", ":")
            )

            print(
                f"\n⛏ Mining Block #{index}"
            )

            print(
                f"🎯 Difficulty: {difficulty}"
            )

            nonce = 0

            hashes = 0

            start = time.time()

            target = "0" * difficulty

            # =============================================
            # MINING LOOP
            # =============================================

            while running:

                # =========================================
                # TEMPLATE REFRESH
                # =========================================

                if (
                    nonce %
                    TEMPLATE_REFRESH_NONCE
                    == 0
                ):

                    try:

                        latest = get_template()

                        # stale block fix
                        if (
                            latest["prev_hash"]
                            != prev_hash
                        ):

                            print(
                                "\n🔄 New block detected"
                            )

                            break

                    except Exception as e:

                        print(
                            "⚠️ Refresh error:",
                            e
                        )

                # =========================================
                # BUILD BLOCK HASH
                # =========================================

                block_data = (

                    f"{index}"
                    f"{prev_hash}"
                    f"{timestamp}"
                    f"{nonce}"
                    f"{tx_str}"

                )

                h = double_sha256(
                    block_data
                )

                hashes += 1
                shares += 1

                # =========================================
                # HASHRATE
                # =========================================

                if (
                    hashes %
                    HASH_UPDATE_INTERVAL
                    == 0
                ):

                    elapsed = (
                        time.time() - start
                    )

                    if elapsed <= 0:
                        elapsed = 1

                    hr = int(
                        hashes / elapsed
                    )

                    current_hashrate = hr

                    print(
                        f"⚡ {hr:,} H/s "
                        f"| Nonce {nonce}"
                    )

                    send_hashrate(
                        hr,
                        shares
                    )

                # =========================================
                # BLOCK FOUND
                # =========================================

                if h.startswith(target):

                    elapsed = round(
                        time.time() - start,
                        2
                    )

                    print("\n🔥 BLOCK FOUND")

                    print(
                        "🧱 Hash:",
                        h
                    )

                    print(
                        "🔢 Nonce:",
                        nonce
                    )

                    print(
                        "⏱ Time:",
                        elapsed,
                        "sec"
                    )

                    block = {

                        "index":
                        index,

                        "previous_hash":
                        prev_hash,

                        "timestamp":
                        timestamp,

                        "nonce":
                        nonce,

                        "transactions":
                        txs,

                        "difficulty":
                        difficulty,

                        "hash":
                        h
                    }

                    # =====================================
                    # SUBMIT BLOCK
                    # =====================================

                    result = submit_block(
                        block
                    )

                    print(
                        "📨 RESULT:",
                        result
                    )

                    # =====================================
                    # SUCCESS
                    # =====================================

                    if (
                        isinstance(result, dict)
                        and
                        result.get("status")
                        == "accepted"
                    ):

                        print(
                            "✅ BLOCK ACCEPTED"
                        )

                    else:

                        print(
                            "❌ BLOCK REJECTED"
                        )

                    # ALWAYS NEW TEMPLATE
                    break

                nonce += 1

                # overflow protection
                if nonce >= MAX_NONCE:

                    nonce = 0

        except KeyboardInterrupt:

            print(
                "\n🛑 Miner stopped"
            )

            break

        except Exception as e:

            print(
                "❌ Miner error:",
                e
            )

            time.sleep(
                AUTO_RECONNECT_DELAY
            )

# =========================================================
# 🚀 START
# =========================================================

if __name__ == "__main__":

    mine()
