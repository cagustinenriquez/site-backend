import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from app.auth import get_password_hash, verify_admin_password, verify_password

USERS_FILE = Path("data") / "users.json"
FALLBACK_USERNAME = "admin"


class User(BaseModel):
    username: str
    hashed_password: str


def _load_users() -> dict:
    if not USERS_FILE.exists():
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users: dict):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def get_user(username: str) -> Optional[User]:
    user_data = _load_users().get(username)
    return User(**user_data) if user_data else None


def user_exists(username: str) -> bool:
    """Whether tokens for this username should still be accepted.

    While there are no users, only the "admin" fallback exists. Once
    users.json has users, "admin" (fallback) tokens and tokens for removed
    users stop working.
    """
    users = _load_users()
    if not users:
        return username == FALLBACK_USERNAME
    return username in users


def authenticate_user(username: str, password: str) -> Optional[str]:
    """Return the username if the credentials are valid, else None.

    Users live in data/users.json (create them with scripts/create_user.py).
    Until that file has any users, "admin" + ADMIN_PASSWORD works instead, so
    a fresh install or Docker container can still log in.
    """
    users = _load_users()
    if not users:
        if username == FALLBACK_USERNAME and verify_admin_password(password):
            return username
        return None

    user_data = users.get(username)
    if user_data and verify_password(password, user_data["hashed_password"]):
        return username
    return None


def create_user(username: str, password: str) -> User:
    users = _load_users()
    if username in users:
        raise ValueError(f"User {username} already exists")
    user = User(username=username, hashed_password=get_password_hash(password))
    users[username] = user.model_dump()
    _save_users(users)
    return user
