from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.auth import create_access_token, Token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.users import authenticate_user
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """
    Login endpoint - returns JWT token for authentication.

    Accepts username and password, returns JWT token:
    ```
    Authorization: Bearer <token>
    ```
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
    return {"access_token": access_token, "token_type": "bearer"}
