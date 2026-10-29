from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from app.auth import (
    create_access_token,
    verify_admin_password,
    Token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from datetime import timedelta
from app.config import settings
from app.limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


@router.post("/login", response_model=Token)
@limiter.limit(settings.rate_limit_login)
async def login(request: Request, credentials: LoginRequest):
    """
    Login endpoint - returns JWT token for authentication.

    Use the admin password to get a token, then include it in subsequent requests:
    ```
    Authorization: Bearer <token>
    ```
    """
    if not verify_admin_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": "admin"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
