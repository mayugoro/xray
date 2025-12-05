import json
import os
from datetime import datetime, timedelta

DATABASE_FILE = "users.json"

def load_users():
    """Load users from JSON database"""
    if not os.path.exists(DATABASE_FILE):
        return {}
    with open(DATABASE_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    """Save users to JSON database"""
    with open(DATABASE_FILE, 'w') as f:
        json.dump(users, indent=2, fp=f)

def add_user(username, uuid, days=30):
    """Add new VMess user"""
    users = load_users()
    expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    
    users[username] = {
        "uuid": uuid,
        "username": username,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expiry_date": expiry_date,
        "days": days,
        "active": True
    }
    save_users(users)
    return users[username]

def get_user(username):
    """Get user by username"""
    users = load_users()
    return users.get(username)

def delete_user(username):
    """Delete user by username"""
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        return True
    return False

def list_users():
    """List all users"""
    return load_users()

def is_user_expired(username):
    """Check if user is expired"""
    user = get_user(username)
    if not user:
        return True
    
    expiry = datetime.strptime(user['expiry_date'], "%Y-%m-%d")
    return datetime.now() > expiry
