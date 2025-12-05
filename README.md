# VMess Bot Manager

Bot Telegram untuk mengelola akun VMess di XRay dengan mudah.

## Fitur

- ➕ Create akun VMess baru
- 📋 List semua akun
- 🗑 Delete akun
- ℹ️ Info akun + generate VMess link
- 🔗 Auto-generate VMess link dengan IP VPS

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Konfigurasi

Edit file `.env` dan isi:

```env
BOT_TOKEN="your_bot_token"
ADMIN_ID="your_telegram_id"
VPS_IP="192.168.1.1"  # IP VPS Anda
VMESS_PORT="443"       # Port VMess (default 443)
```

### 3. Setup XRay di VPS

Pastikan XRay sudah terinstall di VPS Anda. Config XRay akan berada di `/usr/local/etc/xray/config.json`.

Contoh konfigurasi dasar XRay untuk VMess:

```json
{
  "inbounds": [{
    "port": 443,
    "protocol": "vmess",
    "settings": {
      "clients": []
    },
    "streamSettings": {
      "network": "tcp",
      "security": "none"
    }
  }],
  "outbounds": [{
    "protocol": "freedom"
  }]
}
```

### 4. Jalankan Bot

**Di Windows (untuk testing lokal):**
```bash
python bot.py
```

**Di VPS Linux:**
```bash
python3 bot.py
```

Atau gunakan screen/tmux untuk menjalankan di background:
```bash
screen -S vmess-bot
python3 bot.py
# Tekan Ctrl+A+D untuk detach
```

## Cara Menggunakan Bot

1. **Start Bot**: Kirim `/start` ke bot
2. **Create User**: 
   - Kirim `/create`
   - Masukkan email user
   - Masukkan durasi hari (contoh: 30)
   - Bot akan generate VMess link
3. **List Users**: Kirim `/list` untuk melihat semua user
4. **Get Info**: Kirim `/info email@example.com` untuk info detail
5. **Delete User**: Kirim `/delete` dan masukkan email

## Struktur File

```
v2ray_xray_project/
├── bot.py              # Main bot file
├── config.py           # Configuration loader
├── database.py         # JSON database handler
├── xray_manager.py     # XRay config management
├── utils.py            # Utility functions
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── users.json         # User database (auto-generated)
└── README.md          # This file
```

## Keamanan

- Bot hanya bisa digunakan oleh Admin (berdasarkan ADMIN_ID)
- Pastikan `.env` tidak di-commit ke git
- VMess menggunakan UUID random untuk setiap user
- Data user disimpan di `users.json` dengan informasi expiry date

## Troubleshooting

**Bot tidak bisa add/remove user di XRay:**
- Pastikan bot dijalankan dengan permission yang tepat (bisa akses `/usr/local/etc/xray/config.json`)
- Pastikan XRay service berjalan (`systemctl status xray`)
- Cek log error saat bot jalan

**VMess link tidak bisa connect:**
- Pastikan IP VPS sudah benar di `.env`
- Cek firewall VPS, pastikan port VMess (443) terbuka
- Pastikan XRay service berjalan
- Test dengan command: `systemctl status xray`

## Catatan

- VMess link menggunakan IP VPS langsung (tanpa domain)
- Port default adalah 443 (bisa diganti di `.env`)
- Security default: none (VMess sudah ada encryption)
- Network: TCP
- AlterID: 0 (AEAD encryption)

## Support

Jika ada masalah, cek:
1. Log bot saat running
2. XRay logs: `journalctl -u xray -f`
3. Pastikan semua dependencies terinstall
4. Pastikan config XRay sudah benar
