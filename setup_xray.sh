#!/bin/bash
# Script untuk setup XRay dengan bug host support

echo "=== XRay Bug Host Setup ==="
echo ""

# Backup config lama
if [ -f /usr/local/etc/xray/config.json ]; then
    cp /usr/local/etc/xray/config.json /usr/local/etc/xray/config.json.backup
    echo "✓ Backup config lama"
fi

# Buat config baru
cat > /usr/local/etc/xray/config.json << 'EOF'
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
          "acceptProxyProtocol": false,
          "path": "/vmess"
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
EOF

echo "✓ Config XRay dibuat"

# Set permission
chmod 644 /usr/local/etc/xray/config.json
echo "✓ Permission di-set"

# Restart XRay
systemctl restart xray
sleep 2

# Cek status
if systemctl is-active --quiet xray; then
    echo "✓ XRay berjalan"
else
    echo "✗ XRay error, cek log:"
    journalctl -u xray -n 20 --no-pager
    exit 1
fi

# Cek port
if netstat -tuln | grep -q ":54354"; then
    echo "✓ Port 54354 listening"
else
    echo "✗ Port 54354 tidak listening"
    exit 1
fi

echo ""
echo "=== Setup selesai! ==="
echo "Sekarang jalankan bot Telegram dan buat akun baru"
