from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.storage import Database
import secrets
from app.config import settings
from app.db import get_db

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days

# Password hashing for users in the users table
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    sub: Optional[str] = None


def verify_admin_password(password: str) -> bool:
    """Check a password against ADMIN_PASSWORD in constant time"""
    return secrets.compare_digest(
        password.encode("utf-8"), settings.admin_password.encode("utf-8")
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a password against an argon2 hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password with argon2"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    to_encode["token_type"] = "access"
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a longer-lived JWT used only to get new access tokens"""
    to_encode = data.copy()
    to_encode["token_type"] = "refresh"
    to_encode["exp"] = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """Verify a JWT of the given type and return its subject"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        # Tokens issued before refresh tokens existed have no type: treat as access
        if username is None or payload.get("token_type", "access") != token_type:
            return None
        return username
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_db),
) -> str:
    """Dependency to verify JWT token from Authorization header"""
    # Imported here because app.users imports from this module
    from app.users import user_exists

    token = credentials.credentials
    username = verify_token(token)
    if username is None or not user_exists(db, username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username
