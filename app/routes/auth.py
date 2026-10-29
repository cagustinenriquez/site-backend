from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.config import settings
from app.db import get_db
from app.limiter import limiter
from app.users import FALLBACK_USERNAME, authenticate_user, user_exists

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = FALLBACK_USERNAME
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _issue_tokens(username: str) -> dict:
    return {
        "access_token": create_access_token(
            data={"sub": username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        ),
        "refresh_token": create_refresh_token(data={"sub": username}),
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
@limiter.limit(settings.rate_limit_login)
def login(
    request: Request, credentials: LoginRequest, db: Session = Depends(get_db)
):
    """
    Login with username and password. Returns:
    - access_token: send as `Authorization: Bearer <token>` (30 min)
    - refresh_token: send to /auth/refresh for a new access token (7 days)
    """
    username = authenticate_user(db, credentials.username, credentials.password)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return _issue_tokens(username)


@router.post("/refresh", response_model=Token)
@limiter.limit(settings.rate_limit_login)
def refresh(
    request: Request, body: RefreshRequest, db: Session = Depends(get_db)
):
    """Swap a valid refresh token for a new access token and refresh token"""
    username = verify_token(body.refresh_token, token_type="refresh")
    if not username or not user_exists(db, username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return _issue_tokens(username)
