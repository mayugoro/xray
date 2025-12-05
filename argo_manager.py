import subprocess
import json
import os
from config import CLOUDFLARED_PATH, XRAY_LOCAL_PORT

def install_cloudflared():
    """Install cloudflared if not exists"""
    if os.path.exists(CLOUDFLARED_PATH):
        return True, "Cloudflared already installed"
    
    try:
        # Detect architecture
        arch_cmd = subprocess.run(['uname', '-m'], capture_output=True, text=True)
        arch = arch_cmd.stdout.strip()
        
        # Download cloudflared
        if arch in ['x86_64', 'amd64']:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        elif arch in ['aarch64', 'arm64']:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
        elif arch in ['armv7l']:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
        else:
            return False, f"Unsupported architecture: {arch}"
        
        # Download
        subprocess.run(['curl', '-L', url, '-o', '/tmp/cloudflared'], check=True)
        subprocess.run(['chmod', '+x', '/tmp/cloudflared'], check=True)
        subprocess.run(['mv', '/tmp/cloudflared', CLOUDFLARED_PATH], check=True)
        
        return True, "Cloudflared installed successfully"
    except Exception as e:
        return False, f"Failed to install cloudflared: {str(e)}"

def create_argo_tunnel(tunnel_name):
    """Create Argo tunnel"""
    try:
        result = subprocess.run(
            [CLOUDFLARED_PATH, 'tunnel', 'create', tunnel_name],
            capture_output=True,
            text=True,
            check=True
        )
        return True, f"Tunnel {tunnel_name} created"
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr:
            return True, f"Tunnel {tunnel_name} already exists"
        return False, e.stderr

def delete_argo_tunnel(tunnel_name):
    """Delete Argo tunnel"""
    try:
        # Cleanup first
        subprocess.run(
            [CLOUDFLARED_PATH, 'tunnel', 'cleanup', tunnel_name],
            capture_output=True,
            text=True
        )
        
        # Delete
        subprocess.run(
            [CLOUDFLARED_PATH, 'tunnel', 'delete', tunnel_name],
            capture_output=True,
            text=True,
            check=True
        )
        return True, f"Tunnel {tunnel_name} deleted"
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def list_argo_tunnels():
    """List all Argo tunnels"""
    try:
        result = subprocess.run(
            [CLOUDFLARED_PATH, 'tunnel', 'list'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def bind_domain_to_tunnel(tunnel_name, domain):
    """Bind domain to Argo tunnel"""
    try:
        result = subprocess.run(
            [CLOUDFLARED_PATH, 'tunnel', 'route', 'dns', tunnel_name, domain],
            capture_output=True,
            text=True,
            check=True
        )
        return True, f"Domain {domain} bound to tunnel {tunnel_name}"
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr:
            return True, f"Domain {domain} already bound"
        return False, e.stderr

def get_tunnel_info(tunnel_name):
    """Get tunnel information"""
    try:
        result = subprocess.run(
            [CLOUDFLARED_PATH, 'tunnel', 'info', tunnel_name],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def start_argo_tunnel(tunnel_name, domain=None):
    """Start Argo tunnel with config"""
    try:
        # Create config
        config_path = f"/tmp/argo_{tunnel_name}.yaml"
        
        # Get tunnel UUID
        list_output = list_argo_tunnels()
        tunnel_id = None
        for line in list_output.split('\n'):
            if tunnel_name in line:
                tunnel_id = line.split()[0]
                break
        
        if not tunnel_id:
            return False, "Tunnel ID not found"
        
        config = {
            'tunnel': tunnel_id,
            'credentials-file': f'/root/.cloudflared/{tunnel_id}.json',
            'ingress': [
                {
                    'service': f'http://localhost:{XRAY_LOCAL_PORT}'
                }
            ]
        }
        
        if domain:
            config['ingress'].insert(0, {
                'hostname': domain,
                'service': f'http://localhost:{XRAY_LOCAL_PORT}'
            })
        
        # Write config
        with open(config_path, 'w') as f:
            import yaml
            yaml.dump(config, f)
        
        # Start tunnel in background
        subprocess.Popen(
            [CLOUDFLARED_PATH, 'tunnel', '--config', config_path, 'run', tunnel_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        return True, f"Tunnel {tunnel_name} started"
    except Exception as e:
        return False, str(e)

def stop_argo_tunnel():
    """Stop all Argo tunnels"""
    try:
        subprocess.run(['pkill', '-f', 'cloudflared'], check=False)
        return True, "Argo tunnels stopped"
    except Exception as e:
        return False, str(e)

def get_quick_tunnel_url():
    """Get quick tunnel URL (temporary tunnel)"""
    try:
        # Start quick tunnel
        process = subprocess.Popen(
            [CLOUDFLARED_PATH, 'tunnel', '--url', f'http://localhost:{XRAY_LOCAL_PORT}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for URL
        import time
        for _ in range(30):
            if process.poll() is not None:
                break
            time.sleep(1)
            
            # Check for trycloudflare.com URL
            try:
                with open('/tmp/cloudflared.log', 'r') as f:
                    content = f.read()
                    if 'trycloudflare.com' in content:
                        import re
                        match = re.search(r'https://[\w-]+\.trycloudflare\.com', content)
                        if match:
                            return True, match.group(0)
            except:
                pass
        
        return False, "Failed to get quick tunnel URL"
    except Exception as e:
        return False, str(e)
