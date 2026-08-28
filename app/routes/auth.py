from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.auth import (
    create_access_token,
    verify_password,
    Token,
    ADMIN_PASSWORD,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """
    Login endpoint - returns JWT token for authentication.

    Use the admin password to get a token, then include it in subsequent requests:
    ```
    Authorization: Bearer <token>
    ```
    """
    if not verify_password(request.password, ADMIN_PASSWORD):
        # Simple check - in production, hash the password in config
        if request.password != ADMIN_PASSWORD:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": "admin"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
