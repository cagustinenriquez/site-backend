"""User accounts (users table)."""
from typing import Optional

from pydantic import BaseModel

from app.auth import get_password_hash, verify_admin_password, verify_password
from app.db_models import UserRow
from app.storage import Database, table

FALLBACK_USERNAME = "admin"


class User(BaseModel):
    username: str
    hashed_password: str


def _users(db: Database):
    return table(db, UserRow)


def get_user(db: Database, username: str) -> Optional[User]:
    row = _users(db).get(username=username)
    return User(**row) if row else None


def user_exists(db: Database, username: str) -> bool:
    """Whether tokens for this username should still be accepted.

    While there are no users, only the "admin" fallback exists. Once the
    users table has users, "admin" (fallback) tokens and tokens for removed
    users stop working.
    """
    if not _users(db).exists():
        return username == FALLBACK_USERNAME
    return get_user(db, username) is not None


def authenticate_user(db: Database, username: str, password: str) -> Optional[str]:
    """Return the username if the credentials are valid, else None.

    Users live in the users table (create them with scripts/create_user.py).
    Until it has any users, "admin" + ADMIN_PASSWORD works instead, so a
    fresh install can still log in.
    """
    if not _users(db).exists():
        if username == FALLBACK_USERNAME and verify_admin_password(password):
            return username
        return None

    user = get_user(db, username)
    if user and verify_password(password, user.hashed_password):
        return username
    return None


def create_user(db: Database, username: str, password: str) -> User:
    if get_user(db, username):
        raise ValueError(f"User {username} already exists")
    row = _users(db).insert(
        {"username": username, "hashed_password": get_password_hash(password)}
    )
    return User(**row)


def delete_user(db: Database, username: str) -> bool:
    return _users(db).delete(username=username)
