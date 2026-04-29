from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from storage.models import AuthRequest, AuthResponse


SECRET = os.getenv("JWT_SECRET", "change-in-production")
USERNAME = os.getenv("OPERATOR_USERNAME", "admin")
PASSWORD = os.getenv("OPERATOR_PASSWORD", "changeme")
TOKEN_EXPIRE_HOURS = 12

security = HTTPBearer()


def create_token() -> str:
    payload = {
        "sub": USERNAME,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def authenticate(credentials: AuthRequest) -> AuthResponse:
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return AuthResponse(token=create_token(), expires_in=TOKEN_EXPIRE_HOURS * 3600)


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    return _decode_token(credentials.credentials)


def verify_ws_token(token: str = Query(...)) -> dict:
    return _decode_token(token)
