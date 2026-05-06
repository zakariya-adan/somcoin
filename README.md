<p align="center">
  <img src="https://somcoin.online/logo.png" width="120">
</p>

<h1 align="center">SomCoin</h1>

<p align="center">
  Fast • Secure • Decentralized
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square">
  <img src="https://img.shields.io/badge/Network-Mainnet-green?style=flat-square">
  <img src="https://img.shields.io/badge/Mining-Enabled-brightgreen?style=flat-square">
</p>

---

# SomCoin

SomCoin is a decentralized cryptocurrency built in Python featuring:

- Proof-of-Work mining
- UTXO transaction model
- Peer-to-peer networking
- Dynamic difficulty adjustment
- ECDSA cryptography
- Multi-node synchronization

Official Website:

👉 https://somcoin.online

---

# Features

- SHA-256 blockchain
- CPU mining
- Block rewards + halving
- Transaction fees
- Mempool system
- Automatic peer discovery
- Chain synchronization
- Double-spend protection
- Secure wallet generation

---

# Project Structure

```bash
somcoin-core/
│
├── somcoin_node.py
├── miner.py
├── install_somcoin.sh
├── requirements.txt
├── README.md
└── .gitignore
```

---

# Installation

Clone repository:

```bash
git clone https://github.com/zakariya-adan/somcoin.git
cd somcoin-core
```

Create virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Run Node

```bash
python3 somcoin_node.py
```

---

# Run Miner

```bash
python3 miner.py
```

---

# Default Ports

| Service | Port |
|---|---|
| API | 9443 |
| P2P | 9334 |

---

# API Endpoints

| Endpoint | Description |
|---|---|
| `/api` | Network information |
| `/chain` | Full blockchain |
| `/mempool` | Pending transactions |
| `/balance/<address>` | Wallet balance |
| `/wallet/new` | Generate wallet |
| `/send` | Broadcast transaction |

---

# Economics

| Item | Value |
|---|---|
| Max Supply | 21,000,000 SOM |
| Consensus | Proof-of-Work |
| Initial Reward | 10 SOM |
| Minimum Reward | 1 SOM |

---

# Security

SomCoin includes:

- ECDSA digital signatures
- UTXO verification
- Anti double-spend protection
- Peer validation
- Anti-spam filtering

---

# License

MIT License

---

# Developer

Zakariya Adan Team

Founder of SomCoin

---
