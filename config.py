import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VPS_IP = os.getenv("VPS_IP", "YOUR_VPS_IP")
BUG_HOST = os.getenv("BUG_HOST", "")
ARGO_DOMAIN = os.getenv("ARGO_DOMAIN", "")  # Cloudflare Argo domain
USE_ARGO = os.getenv("USE_ARGO", "false").lower() == "true"
XRAY_CONFIG_PATH = "/usr/local/etc/xray/config.json"
CLOUDFLARED_PATH = "/usr/local/bin/cloudflared"
VMESS_PORT = int(os.getenv("VMESS_PORT", "443"))
XRAY_LOCAL_PORT = int(os.getenv("XRAY_LOCAL_PORT", "8080"))
