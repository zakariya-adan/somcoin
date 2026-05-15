# =========================================================
# 🚀 ULTRA PRO MAX FINAL MINER (2026)
# =========================================================

import requests
import hashlib
import time
import json
import gc

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

HASH_UPDATE_INTERVAL = 1_000_000

TEMPLATE_REFRESH_NONCE = 500_000

REQUEST_TIMEOUT = 30

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
# 📦 GET BLOCK TEMPLATE
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

def send_hashrate(hr, shares):

    try:

        session.post(
            "https://somcoin.online/submit_miner",
            json={
                "address": ADDRESS,
                "hashrate": hr,
                "shares": shares
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

            # IMPORTANT FIX
            json=block,

            timeout=REQUEST_TIMEOUT
        )

        print("STATUS:", r.status_code)
        print("TEXT:", r.text)

        try:
            return r.json()
        except:
            return {
                "success": False,
                "error": "invalid json"
            }

    except Exception as e:

        print("❌ Submit error:", e)

        return {
            "success": False,
            "error": str(e)
        }


# =========================================================
# ⛏ MINER
# =========================================================

def mine():

    print("🚀 SomCoin Decentralized Miner")
    print("🌐 Node:", NODE_URL)
    print("💰 Address:", ADDRESS)

    while True:

        try:

            # =================================================
            # GET TEMPLATE
            # =================================================

            tpl = get_template()

            index = tpl["index"]
            prev_hash = tpl["prev_hash"]
            difficulty = tpl["difficulty"]
            txs = tpl["transactions"]

            tx_str = json.dumps(
                txs,
                sort_keys=True
            )

            print(f"\n⛏ Mining Block #{index}")
            print(f"🎯 Difficulty: {difficulty}")

            nonce = 0
            hashes = 0

            start = time.time()

            # =================================================
            # MINING LOOP
            # =================================================

            while True:

                # =============================================
                # REFRESH TEMPLATE
                # =============================================

                if nonce % TEMPLATE_REFRESH_NONCE == 0:

                    try:

                        latest = get_template()

                        # chain changed
                        if (
                            latest["prev_hash"]
                            != prev_hash
                        ):

                            print(
                                "🔄 New block detected "
                                "→ restarting mining"
                            )

                            break

                    except:
                        pass

                timestamp = int(time.time())

                block_data = (
                    f"{index}"
                    f"{prev_hash}"
                    f"{timestamp}"
                    f"{nonce}"
                    f"{tx_str}"
                )

                h = double_sha256(block_data)

                hashes += 1

                # =============================================
                # HASHRATE
                # =============================================

                if (
                    hashes
                    % HASH_UPDATE_INTERVAL
                    == 0
                ):

                    elapsed = (
                        time.time() - start
                    )

                    if elapsed > 0:

                        hr = int(
                            hashes / elapsed
                        )

                        print(
                            f"⚡ {hr:,} H/s "
                            f"| Nonce {nonce}"
                        )

                        # dashboard
                        send_hashrate(
                            hr,
                            hashes
                        )

                # =============================================
                # BLOCK FOUND
                # =============================================

                if h.startswith(
                    "0" * difficulty
                ):

                    elapsed = round(
                        time.time() - start,
                        2
                    )

                    print("\n🔥 BLOCK FOUND")
                    print("🧱 Hash:", h)
                    print("🔢 Nonce:", nonce)
                    print("⏱ Time:", elapsed)

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

                    # =========================================
                    # SUBMIT
                    # =========================================

                    result = submit_block(
                        block
                    )

                    print(
                        "📨 RESULT:",
                        result
                    )

                    # IMPORTANT
                    # ALWAYS RESTART TEMPLATE
                    break

                nonce += 1

        # =====================================================
        # CTRL+C
        # =====================================================

        except KeyboardInterrupt:

            print("\n🛑 Miner stopped")
            break

        # =====================================================
        # ERROR
        # =====================================================

        except Exception as e:

            print("❌ Error:", e)

            time.sleep(2)


# =========================================================
# 🚀 START
# =========================================================

if __name__ == "__main__":

    mine()
