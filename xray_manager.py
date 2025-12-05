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
                    "network": "tcp",
                    "security": "none"
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

def add_vmess_user(email, uuid):
    """Add VMess user to XRay config"""
    config = read_xray_config()
    
    # Find VMess inbound
    for inbound in config['inbounds']:
        if inbound.get('protocol') == 'vmess':
            # Check if user already exists
            clients = inbound['settings'].get('clients', [])
            if any(client['email'] == email for client in clients):
                return False, "User already exists"
            
            # Add new client
            clients.append({
                "id": uuid,
                "email": email,
                "alterId": 0
            })
            inbound['settings']['clients'] = clients
            
            write_xray_config(config)
            restart_xray()
            return True, "User added successfully"
    
    return False, "VMess inbound not found"

def remove_vmess_user(email):
    """Remove VMess user from XRay config"""
    config = read_xray_config()
    
    for inbound in config['inbounds']:
        if inbound.get('protocol') == 'vmess':
            clients = inbound['settings'].get('clients', [])
            original_count = len(clients)
            
            # Remove user
            clients = [c for c in clients if c['email'] != email]
            
            if len(clients) < original_count:
                inbound['settings']['clients'] = clients
                write_xray_config(config)
                restart_xray()
                return True, "User removed successfully"
            else:
                return False, "User not found"
    
    return False, "VMess inbound not found"

def get_vmess_users():
    """Get all VMess users from XRay config"""
    config = read_xray_config()
    
    for inbound in config['inbounds']:
        if inbound.get('protocol') == 'vmess':
            return inbound['settings'].get('clients', [])
    
    return []
