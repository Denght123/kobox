from fastapi import Depends, Header, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_language_code(
    lang: str | None = Query(default=None),
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
) -> str:
    if lang:
        return lang
    if accept_language:
        primary = accept_language.split(",")[0].strip()
        return primary or "zh-CN"
    return "zh-CN"


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = get_current_user_id(token)
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise AppException(status_code=401, code="user_not_found", message="User not found")
    if not user.is_active:
        raise AppException(status_code=403, code="inactive_user", message="User is inactive")
    return user


def get_current_user_id(token: str | None = Depends(oauth2_scheme)) -> int:
    if not token:
        raise AppException(status_code=401, code="missing_token", message="Authorization token required")
    claims = decode_token(token)
    if claims.get("type") != "access":
        raise AppException(status_code=401, code="invalid_token_type", message="Not an access token")
    return int(claims.get("sub"))
