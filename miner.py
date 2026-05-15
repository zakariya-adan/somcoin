import requests
import hashlib
import time
import json

# ==========================================
# CONFIG
# ==========================================

NODE_URL = "http://127.0.0.1:9443"
ADDRESS = "SOMGjFnfFWcFTTc7HsftBXdQP4wSDgYyE"

# ==========================================
# DOUBLE SHA256
# ==========================================

def double_sha256(data):
    return hashlib.sha256(
        hashlib.sha256(data.encode()).digest()
    ).hexdigest()

# ==========================================
# GET TEMPLATE
# ==========================================

def get_template():

    r = requests.get(
        f"{NODE_URL}/get_block_template?address={ADDRESS}",
        timeout=120
    )

    return r.json()

# ==========================================
# MINER
# ==========================================

def mine():

    print("🚀 SomCoin Decentralized Miner")
    print("🌐 Node:", NODE_URL)
    print("💰 Address:", ADDRESS)

    while True:

        try:

            # ==========================================
            # GET NEW BLOCK TEMPLATE
            # ==========================================

            tpl = get_template()

            index = tpl["index"]
            prev_hash = tpl["prev_hash"]
            difficulty = tpl["difficulty"]
            txs = tpl["transactions"]

            tx_str = json.dumps(txs, sort_keys=True)

            print(f"\n⛏ Mining Block #{index}")
            print("🎯 Difficulty:", difficulty)

            nonce = 0
            hashes = 0

            start = time.time()

            # ==========================================
            # MINING LOOP
            # ==========================================

            while True:

                # ==========================================
                # CHECK NEW BLOCK EVERY 2 SEC
                # ==========================================

                if nonce % 500000 == 0:

                    try:

                        latest = get_template()

                        # chain changed
                        if latest["prev_hash"] != prev_hash:

                            print("🔄 New block detected → restarting mining")
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

                # ==========================================
                # HASHRATE
                # ==========================================

                if hashes % 100000 == 0:

                    elapsed = time.time() - start

                    if elapsed > 0:

                        hr = int(hashes / elapsed)

                        print(
                            f"⚡ {hr:,} H/s | "
                            f"Nonce {nonce}"
                        )

                        # ==========================================
                        # SEND REAL MINER TO DASHBOARD
                        # ==========================================

                        try:

                            requests.post(
                                "https://somcoin.online/submit_miner",
                                json={

                                    "address": ADDRESS,

                                    "hashrate": hr,

                                    "shares": hashes

                                },
                                timeout=5
                            )

                        except:
                            pass

                # ==========================================
                # BLOCK FOUND
                # ==========================================

                if h.startswith("0" * difficulty):

                    elapsed = round(time.time() - start, 2)

                    print("\n🔥 BLOCK FOUND")
                    print("🧱 Hash:", h)
                    print("🔢 Nonce:", nonce)
                    print("⏱ Time:", elapsed, "sec")

                    block = {
                        "index": index,
                        "previous_hash": prev_hash,
                        "timestamp": timestamp,
                        "nonce": nonce,
                        "transactions": txs,
                        "difficulty": difficulty,
                        "hash": h
                    }

                    # ==========================================
                    # SUBMIT BLOCK
                    # ==========================================

                    try:

                        r = requests.post(
                            f"{NODE_URL}/submit_block",
                            json={"block": block},
                            timeout=600
                        )

                        result = r.json()

                        print("📨 RESULT:", result)

                    except Exception as e:

                        print("⚠️ Submit error:", e)

                    # IMPORTANT
                    # always restart fresh template
                    break

                nonce += 1

        except KeyboardInterrupt:

            print("\n🛑 Miner stopped")
            break

        except Exception as e:

            print("❌ Error:", e)
            time.sleep(2)

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    mine()
