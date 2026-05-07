from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_language_code
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshRequest,
    RegisterRequest,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    language_code: str = Depends(get_language_code),
    db: Session = Depends(get_db),
) -> AuthResponse:
    return AuthService(db).register(payload, language_code=language_code)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    language_code: str = Depends(get_language_code),
    db: Session = Depends(get_db),
) -> AuthResponse:
    return AuthService(db).login(payload, language_code=language_code)


@router.post("/refresh", response_model=AuthResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AuthResponse:
    return AuthService(db).refresh(payload)


@router.post("/logout", response_model=MessageResponse)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> MessageResponse:
    return MessageResponse(**AuthService(db).logout(payload))


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> PasswordResetRequestResponse:
    return AuthService(db).request_password_reset(payload)


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)) -> MessageResponse:
    return MessageResponse(**AuthService(db).reset_password(payload))
