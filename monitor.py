import subprocess
import json
import re
from datetime import datetime

def get_xray_connections():
    """Get active connections from XRay API"""
    try:
        # Query XRay stats API
        result = subprocess.run(
            ['xray', 'api', 'statsquery', '--server=127.0.0.1:10085', '--pattern=""'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return parse_xray_stats(result.stdout)
        return []
    except Exception as e:
        print(f"Error getting XRay connections: {e}")
        return []

def parse_xray_stats(stats_output):
    """Parse XRay stats output"""
    connections = []
    try:
        # Parse user traffic data
        lines = stats_output.strip().split('\n')
        for line in lines:
            if 'user>>>' in line and ('uplink' in line or 'downlink' in line):
                match = re.search(r'user>>>(.+?)>>>(uplink|downlink).+?value:\s*(\d+)', line)
                if match:
                    email = match.group(1)
                    direction = match.group(2)
                    traffic = int(match.group(3))
                    
                    # Find or create connection entry
                    conn = next((c for c in connections if c['email'] == email), None)
                    if not conn:
                        conn = {'email': email, 'uplink': 0, 'downlink': 0}
                        connections.append(conn)
                    
                    conn[direction] = traffic
        
        return connections
    except Exception as e:
        print(f"Error parsing XRay stats: {e}")
        return []

def get_xray_log_connections():
    """Get connections from XRay logs (fallback method)"""
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'xray', '-n', '100', '--no-pager'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        connections = set()
        for line in result.stdout.split('\n'):
            if 'accepted' in line.lower() or 'connection' in line.lower():
                # Try to extract IP or connection info
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    connections.add(match.group(1))
        
        return list(connections)
    except Exception as e:
        print(f"Error reading XRay logs: {e}")
        return []

def format_traffic(bytes_count):
    """Format traffic in human readable format"""
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.2f} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"

def get_active_connections():
    """Get list of active connections with details"""
    connections = []
    
    # Method 1: Try XRay API
    api_connections = get_xray_connections()
    if api_connections:
        for conn in api_connections:
            if conn.get('uplink', 0) > 0 or conn.get('downlink', 0) > 0:
                connections.append({
                    'user': conn['email'],
                    'upload': format_traffic(conn['uplink']),
                    'download': format_traffic(conn['downlink']),
                    'total': format_traffic(conn['uplink'] + conn['downlink'])
                })
    
    # Method 2: Fallback to logs
    if not connections:
        log_connections = get_xray_log_connections()
        for ip in log_connections:
            connections.append({
                'ip': ip,
                'status': 'Active'
            })
    
    return connections

def get_connection_count():
    """Get total active connection count"""
    try:
        # Count established connections on XRay port
        result = subprocess.run(
            ['ss', '-tn', 'sport', '=', ':54354'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Count ESTABLISHED connections
        count = len([line for line in result.stdout.split('\n') if 'ESTAB' in line])
        return count
    except Exception:
        return 0
