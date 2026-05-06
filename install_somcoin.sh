#!/bin/bash

echo "🚀 Installing SomCoin Node..."

# =========================
# UPDATE SYSTEM
# =========================
sudo apt update -y && sudo apt upgrade -y

# =========================
# INSTALL DEPENDENCIES
# =========================
sudo apt install -y python3 python3-pip git ufw

# =========================
# INSTALL PYTHON LIBS
# =========================
pip3 install flask requests ecdsa flask-cors

# =========================
# DOWNLOAD PROJECT
# =========================
cd /root

if [ -d "somcoin-core" ]; then
    rm -rf somcoin-core
fi

git clone https://github.com/zakariya-adan/somcoin.git somcoin-core

cd somcoin-core

# =========================
# CREATE SYSTEMD SERVICE
# =========================
sudo bash -c 'cat > /etc/systemd/system/somcoin.service <<EOF
[Unit]
Description=SomCoin Node
After=network.target

[Service]
User=root
WorkingDirectory=/root/somcoin-core
ExecStart=/usr/bin/python3 somcoin_node.py
Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF'

# =========================
# START SERVICE
# =========================
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable somcoin
sudo systemctl start somcoin

# =========================
# FIREWALL
# =========================
sudo ufw allow 9443/tcp
sudo ufw allow 9334/tcp
sudo ufw --force enable

echo "✅ SomCoin Node Installed & Running!"
echo "🌐 API: http://$(curl -s ifconfig.me):9443/api"
