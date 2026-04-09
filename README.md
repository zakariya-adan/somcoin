# UPDATED 2026
🚀 SomCoin

SomCoin is a fully decentralized cryptocurrency built from scratch using Python.
It includes advanced blockchain architecture, UTXO transaction model, Proof-of-Work mining, and secure peer-to-peer networking.

🌐 Official Website: https://somcoin.online

---

🌍 Overview

SomCoin is designed as a real-world blockchain system with production-level features:

- 💸 Secure transactions (ECDSA cryptography)
- ⛏️ Multi-core CPU mining
- 🔐 Wallet system (private/public keys)
- 🌐 Peer-to-peer decentralized network
- 📊 Real-time blockchain & mempool tracking
- 🧠 UTXO model (similar to Bitcoin)

---

⚙️ Core Features

🔗 Blockchain Engine

- SHA-256 hashing
- Block validation system
- Automatic chain replacement
- Dynamic difficulty adjustment

💰 Transaction System

- UTXO-based transactions
- Transaction fees
- Double-spend protection
- Mempool filtering & cleaning

🔐 Security

- ECDSA digital signatures
- Node identity verification (anti-fake nodes)
- Input/output validation
- Anti-spam protections

🌐 P2P Network

- Auto peer discovery
- Seed node connection
- Block & transaction broadcasting
- Chain synchronization

⛏️ Mining System

- Multi-process CPU mining
- Dynamic difficulty scaling
- Block rewards + halving
- Max supply control (21M)

---

🧠 How It Works

1. User creates a wallet (private/public key)
2. Transactions are signed using private key
3. Transactions go into mempool
4. Miners collect and validate transactions
5. Blocks are mined using Proof-of-Work
6. Blocks are broadcast to all peers
7. Network stays synchronized automatically

---

📁 Project Structure

somcoin-core/
│
├── somcoin_node.py      # 🔥 Main node (API + mining + P2P)
├── auto_tx.py           # Auto transaction system
├── templates/           # Web wallet UI
├── private/             # 🔒 Private keys (NOT pushed)
├── backup/              # Backup data
├── blockchain.json      # Blockchain data
├── mempool.json         # Pending transactions
├── peers.json           # Peer list
└── README.md

---

🚀 Installation

1. Clone Repository

git clone https://github.com/zakariya-adan/somcoin.git
cd somcoin-core

2. Setup Virtual Environment

python3 -m venv venv
source venv/bin/activate

3. Install Dependencies

pip install flask flask-cors requests ecdsa

---

▶️ Run Node

python3 somcoin_node.py

Default Ports:

- 🌐 API: "9443"
- 🔗 P2P: "9334"

---

🌐 API Endpoints

Endpoint| Description
"/api"| Network info
"/mine/<address>"| Mine block
"/send"| Send transaction
"/balance/<addr>"| Check balance
"/chain"| Full blockchain
"/mempool"| Pending transactions
"/peers"| Connected peers
"/wallet/new"| Generate wallet

---

🔐 Security Model

SomCoin uses multiple layers of protection:

- ✔ Digital signatures (ECDSA)
- ✔ UTXO validation system
- ✔ Anti double-spend protection
- ✔ Node identity verification
- ✔ Peer filtering & banning system

---

💎 Economics

- Initial reward: 50 SOM
- Minimum reward: 1 SOM
- Max supply: 21,000,000 SOM
- Halving: automatic (block-based)
- Transaction fees included

---

📊 Advanced Features

- ⚡ Hashrate calculation
- 📈 Rich list (top holders)
- 🔎 Transaction search system
- 🌐 Multi-node mining (load balancing)
- 🤖 Auto mining system

---

🌐 Website

Visit official platform:

👉 https://somcoin.online

Features:

- Wallet interface
- Mining dashboard
- Blockchain data viewer

---

📌 Roadmap

- [ ] Mobile wallet app
- [ ] Blockchain explorer website
- [ ] Smart contract support
- [ ] Token system
- [ ] Exchange listing

---

👨‍💻 Created By

Zakariya Adan Team

Founder & Developer of SomCoin

---

📜 License

MIT License

---

⚡ Vision

SomCoin aims to become a fully decentralized cryptocurrency network built independently, demonstrating real blockchain infrastructure including mining, networking, and secure transactions.

---
