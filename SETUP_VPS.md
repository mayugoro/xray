# Setup XRay di VPS

## 1. Install XRay

```bash
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
```

## 2. Buat Config XRay Manual

Edit file `/usr/local/etc/xray/config.json`:

```bash
nano /usr/local/etc/xray/config.json
```

Isi dengan config berikut (sesuaikan port dengan `.env`):

```json
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": 54354,
      "listen": "0.0.0.0",
      "protocol": "vmess",
      "settings": {
        "clients": []
      },
      "streamSettings": {
        "network": "ws",
        "wsSettings": {
          "path": "/vmess",
          "headers": {}
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "settings": {}
    }
  ]
}
```

## 3. Set Permission

```bash
chmod 644 /usr/local/etc/xray/config.json
```

## 4. Enable & Start XRay

```bash
systemctl enable xray
systemctl start xray
systemctl status xray
```

## 5. Buka Firewall

```bash
# UFW
ufw allow 54354/tcp

# Atau iptables
iptables -A INPUT -p tcp --dport 54354 -j ACCEPT
```

## 6. Test XRay

```bash
# Cek apakah XRay berjalan
systemctl status xray

# Cek log jika ada error
journalctl -u xray -f
```

## 7. Install Bot

```bash
cd ~
git clone https://github.com/mayugoro/xray.git
cd xray

# Install Python dependencies
apt install python3-pip -y
pip3 install -r requirements.txt

# Edit .env jika perlu
nano .env
```

## 8. Jalankan Bot

```bash
# Test manual
python3 main.py

# Atau gunakan screen
screen -S vmess-bot
python3 main.py
# Tekan Ctrl+A+D untuk detach
```

## 9. Auto Start Bot (Optional)

Buat systemd service:

```bash
nano /etc/systemd/system/vmess-bot.service
```

Isi:

```ini
[Unit]
Description=VMess Telegram Bot
After=network.target xray.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/xray
ExecStart=/usr/bin/python3 /root/xray/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable service:

```bash
systemctl daemon-reload
systemctl enable vmess-bot
systemctl start vmess-bot
systemctl status vmess-bot
```

## Troubleshooting

### Bot tidak bisa add/remove user
- Pastikan bot jalan dengan permission root atau user yang bisa akses `/usr/local/etc/xray/config.json`
- Cek permission file: `ls -la /usr/local/etc/xray/config.json`

### VMess tidak connect
1. Cek XRay status: `systemctl status xray`
2. Cek log XRay: `journalctl -u xray -f`
3. Cek firewall: `ufw status` atau `iptables -L`
4. Pastikan port 54354 terbuka di panel VPS/cloud provider
5. Test port: `netstat -tuln | grep 54354`

### Update Bot
```bash
cd ~/xray
git pull
systemctl restart vmess-bot  # jika pakai systemd
# atau restart manual screen session
```
