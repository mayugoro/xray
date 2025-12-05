import json
import subprocess
import uuid as uuid_lib
from config import XRAY_CONFIG_PATH

def generate_uuid():
    """Generate random UUID for VMess"""
    return str(uuid_lib.uuid4())

def read_xray_config():
    """Read XRay config from server"""
    try:
        with open(XRAY_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default config if file doesn't exist
        return {
            "inbounds": [{
                "port": 443,
                "protocol": "vmess",
                "settings": {
                    "clients": []
                },
                "streamSettings": {
                    "network": "ws",
                    "security": "none",
                    "wsSettings": {
                        "path": "/vmess"
                    }
                }
            }],
            "outbounds": [{
                "protocol": "freedom"
            }]
        }

def write_xray_config(config):
    """Write XRay config to server"""
    with open(XRAY_CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

def restart_xray():
    """Restart XRay service"""
    try:
        subprocess.run(['systemctl', 'restart', 'xray'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def add_vmess_user(username, uuid):
    """Add VMess user to XRay config"""
    config = read_xray_config()
    
    # Find VMess inbound
    for inbound in config['inbounds']:
        if inbound.get('protocol') == 'vmess':
            # Check if user already exists
            clients = inbound['settings'].get('clients', [])
            if any(client.get('id') == uuid for client in clients):
                return False, "User already exists"
            
            # Add new client (no email field needed)
            clients.append({
                "id": uuid,
                "alterId": 0
            })
            inbound['settings']['clients'] = clients
            
            write_xray_config(config)
            restart_xray()
            return True, "User added successfully"
    
    return False, "VMess inbound not found"

def remove_vmess_user(username):
    """Remove VMess user from XRay config by UUID"""
    # Get user's UUID from database
    from database import get_user
    user = get_user(username)
    if not user:
        return False, "User not found in database"
    
    uuid = user['uuid']
    config = read_xray_config()
    
    for inbound in config['inbounds']:
        if inbound.get('protocol') == 'vmess':
            clients = inbound['settings'].get('clients', [])
            original_count = len(clients)
            
            # Remove user by UUID
            clients = [c for c in clients if c.get('id') != uuid]
            
            if len(clients) < original_count:
                inbound['settings']['clients'] = clients
                write_xray_config(config)
                restart_xray()
                return True, "User removed successfully"
            else:
                return False, "User not found in XRay config"
    
    return False, "VMess inbound not found"

def get_vmess_users():
    """Get all VMess users from XRay config"""
    config = read_xray_config()
    
    for inbound in config['inbounds']:
        if inbound.get('protocol') == 'vmess':
            return inbound['settings'].get('clients', [])
    
    return []
