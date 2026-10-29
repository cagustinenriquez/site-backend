"""User accounts (users table)."""
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.auth import get_password_hash, verify_admin_password, verify_password
from app.db_models import UserRow

FALLBACK_USERNAME = "admin"


class User(BaseModel):
    username: str
    hashed_password: str


def _has_users(db: Session) -> bool:
    return db.scalar(select(exists().select_from(UserRow)))


def get_user(db: Session, username: str) -> Optional[User]:
    row = db.get(UserRow, username)
    return User(username=row.username, hashed_password=row.hashed_password) if row else None


def user_exists(db: Session, username: str) -> bool:
    """Whether tokens for this username should still be accepted.

    While there are no users, only the "admin" fallback exists. Once the
    users table has users, "admin" (fallback) tokens and tokens for removed
    users stop working.
    """
    if not _has_users(db):
        return username == FALLBACK_USERNAME
    return db.get(UserRow, username) is not None


def authenticate_user(db: Session, username: str, password: str) -> Optional[str]:
    """Return the username if the credentials are valid, else None.

    Users live in the users table (create them with scripts/create_user.py).
    Until it has any users, "admin" + ADMIN_PASSWORD works instead, so a
    fresh install can still log in.
    """
    if not _has_users(db):
        if username == FALLBACK_USERNAME and verify_admin_password(password):
            return username
        return None

    row = db.get(UserRow, username)
    if row and verify_password(password, row.hashed_password):
        return username
    return None


def create_user(db: Session, username: str, password: str) -> User:
    if db.get(UserRow, username):
        raise ValueError(f"User {username} already exists")
    row = UserRow(username=username, hashed_password=get_password_hash(password))
    db.add(row)
    db.commit()
    return User(username=row.username, hashed_password=row.hashed_password)


def delete_user(db: Session, username: str) -> bool:
    row = db.get(UserRow, username)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
