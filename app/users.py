import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from app.auth import verify_password, get_password_hash
from app.config import DATA_DIR

USERS_FILE = DATA_DIR / "users.json"


class User(BaseModel):
    username: str
    hashed_password: str


def _load_users() -> dict:
    """Load all users from JSON file"""
    if not USERS_FILE.exists():
        return {}

    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users: dict):
    """Save users to JSON file"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def get_user(username: str) -> Optional[User]:
    """Get a user by username"""
    users = _load_users()
    user_data = users.get(username)
    if not user_data:
        return None
    return User(**user_data)


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user by username and password"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(username: str, password: str) -> User:
    """Create a new user"""
    users = _load_users()

    if username in users:
        raise ValueError(f"User {username} already exists")

    hashed_password = get_password_hash(password)
    user = User(username=username, hashed_password=hashed_password)

    users[username] = user.model_dump()
    _save_users(users)

    return user
