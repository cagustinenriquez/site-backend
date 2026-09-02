from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    Token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.users import authenticate_user
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """
    Login endpoint - returns access and refresh tokens.

    Accepts username and password, returns both tokens:
    - access_token: Use in Authorization header (30 min expiry)
    - refresh_token: Use to get new access token (7 day expiry)
    """
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh(request: RefreshRequest):
    """
    Refresh endpoint - returns new access token using refresh token.

    Use this when your access token expires (every 30 minutes).
    The refresh token lasts 7 days.
    """
    username = verify_token(request.refresh_token, token_type="refresh")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
