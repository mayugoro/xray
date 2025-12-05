import json
import base64
from config import VPS_IP, VMESS_PORT, BUG_HOST, ARGO_DOMAIN, USE_ARGO

def generate_vmess_link(username, uuid, use_argo=None):
    """Generate VMess link - supports Direct, Bug Host, and Argo Tunnel modes"""
    
    # Determine mode
    if use_argo is None:
        use_argo = USE_ARGO
    
    if use_argo and ARGO_DOMAIN:
        # Argo Tunnel Mode
        address = ARGO_DOMAIN
        host_header = ARGO_DOMAIN
        port = "443"  # Argo uses 443 with TLS
        tls = "tls"
        sni = ARGO_DOMAIN
    elif BUG_HOST and BUG_HOST.strip():
        # Bug Host Mode
        address = BUG_HOST
        host_header = VPS_IP
        port = "80"
        tls = ""
        sni = ""
    else:
        # Direct Mode
        address = VPS_IP
        host_header = ""
        port = str(VMESS_PORT)
        tls = ""
        sni = ""
    
    vmess_config = {
        "v": "2",
        "ps": f"{username} ({'Argo' if use_argo and ARGO_DOMAIN else 'Direct'})",
        "add": address,
        "port": port,
        "id": uuid,
        "aid": "0",
        "scy": "auto",
        "net": "ws",
        "type": "none",
        "host": host_header,
        "path": "/vmess",
        "tls": tls,
        "sni": sni,
        "alpn": ""
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
