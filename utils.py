import json
import base64
from config import VPS_IP, VMESS_PORT

def generate_vmess_link(username, uuid):
    """Generate VMess link from user data (WebSocket tunneling support)"""
    vmess_config = {
        "v": "2",
        "ps": username,
        "add": VPS_IP,
        "port": str(VMESS_PORT),
        "id": uuid,
        "aid": "0",
        "net": "ws",
        "type": "none",
        "host": "",
        "path": "/vmess",
        "tls": "none",
        "sni": ""
    }
    
    # Convert to JSON and encode to base64
    json_str = json.dumps(vmess_config)
    encoded = base64.b64encode(json_str.encode()).decode()
    
    return f"vmess://{encoded}"

def decode_vmess_link(vmess_link):
    """Decode VMess link to readable format"""
    if not vmess_link.startswith("vmess://"):
        return None
    
    try:
        encoded = vmess_link[8:]  # Remove "vmess://"
        decoded = base64.b64decode(encoded).decode()
        return json.loads(decoded)
    except Exception:
        return None

def format_user_info(user, uuid):
    """Format user information for display"""
    info = f"👤 Username: `{user['username']}`\n"
    info += f"🆔 UUID: `{uuid}`\n"
    info += f"📅 Created: {user['created_at']}\n"
    info += f"⏰ Expires: {user['expiry_date']}\n"
    info += f"⏳ Duration: {user['days']} days\n"
    info += f"✅ Status: {'Active' if user['active'] else 'Inactive'}\n"
    return info
