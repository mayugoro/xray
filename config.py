import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VPS_IP = os.getenv("VPS_IP", "YOUR_VPS_IP")
XRAY_CONFIG_PATH = "/usr/local/etc/xray/config.json"
VMESS_PORT = int(os.getenv("VMESS_PORT", "443"))
