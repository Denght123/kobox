from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import AppException

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def _build_token(payload: dict[str, Any], expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    token_payload = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(token_payload, settings.secret_key, algorithm="HS256")


def create_access_token(*, user_id: int, username: str) -> str:
    settings = get_settings()
    return _build_token(
        {"sub": str(user_id), "username": username, "type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(*, user_id: int, username: str, jti: str | None = None) -> tuple[str, str]:
    settings = get_settings()
    refresh_jti = jti or str(uuid4())
    token = _build_token(
        {"sub": str(user_id), "username": username, "type": "refresh", "jti": refresh_jti},
        timedelta(days=settings.refresh_token_expire_days),
    )
    return token, refresh_jti


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError as exc:
        raise AppException(code="invalid_token", message="Invalid or expired token", status_code=401) from exc
