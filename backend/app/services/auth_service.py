from datetime import datetime, timedelta, timezone
import hashlib
import re
import secrets
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.user import User
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthResponse,
    AuthUser,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshRequest,
    RegisterRequest,
)
from app.services.mail_service import MailService
from app.services.user_service import UserService


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip()).strip("-").lower()
    return slug or "user"


PASSWORD_RESET_REQUEST_COOLDOWN_SECONDS = 60


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.analytics_repo = AnalyticsRepository(db)
        self.refresh_repo = RefreshTokenRepository(db)
        self.password_reset_repo = PasswordResetRepository(db)
        self.settings = get_settings()

    def _build_auth_response(
        self,
        user: User,
        *,
        dashboard_language_code: str | None = None,
    ) -> AuthResponse:
        access_token = create_access_token(user_id=user.id, username=user.username)
        refresh_token, jti = create_refresh_token(user_id=user.id, username=user.username)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.settings.refresh_token_expire_days
        )
        self.refresh_repo.create(user_id=user.id, token_jti=jti, expires_at=expires_at)
        self.db.commit()
        dashboard = (
            UserService(self.db).get_dashboard(user, language_code=dashboard_language_code)
            if dashboard_language_code
            else None
        )
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=AuthUser(
                id=user.id,
                username=user.username,
                public_slug=user.profile.public_slug,
                display_name=user.profile.display_name,
                avatar_url=user.profile.avatar_url,
                background_image_url=user.profile.background_image_url,
                birthday=user.profile.birthday,
                bio=user.profile.bio,
                is_public=user.profile.is_public,
            ),
            dashboard=dashboard,
        )

    def register(self, payload: RegisterRequest, *, language_code: str | None = None) -> AuthResponse:
        if self.user_repo.get_by_email(payload.email):
            raise AppException(status_code=409, code="email_taken", message="Email already registered")
        if self.user_repo.get_by_username(payload.username):
            raise AppException(status_code=409, code="username_taken", message="Username already registered")

        display_name = payload.display_name or payload.username
        base_slug = _slugify(payload.username)
        slug = base_slug
        suffix = 1
        while self.user_repo.get_by_public_slug(slug):
            suffix += 1
            slug = f"{base_slug}-{suffix}"

        user = self.user_repo.create(
            email=payload.email,
            username=payload.username,
            password_hash=hash_password(payload.password),
            display_name=display_name,
            public_slug=slug,
        )
        self.analytics_repo.record_event(
            event_name="user_registered",
            user_id=user.id,
            metadata={"username": user.username, "public_slug": slug},
        )
        return self._build_auth_response(user, dashboard_language_code=language_code)

    def login(self, payload: LoginRequest, *, language_code: str | None = None) -> AuthResponse:
        user = self.user_repo.get_by_identifier(payload.account)
        if not user or not verify_password(payload.password, user.password_hash):
            raise AppException(status_code=401, code="invalid_credentials", message="Invalid credentials")
        if not user.is_active:
            raise AppException(status_code=403, code="inactive_user", message="User is inactive")
        return self._build_auth_response(user, dashboard_language_code=language_code)

    def refresh(self, payload: RefreshRequest) -> AuthResponse:
        claims = decode_token(payload.refresh_token)
        if claims.get("type") != "refresh":
            raise AppException(status_code=401, code="invalid_token_type", message="Not a refresh token")

        jti = claims.get("jti")
        user_id = int(claims.get("sub"))
        if not jti:
            raise AppException(status_code=401, code="invalid_token", message="Refresh token missing jti")

        token = self.refresh_repo.get_by_jti(jti)
        if token is None or token.revoked_at is not None:
            raise AppException(status_code=401, code="refresh_revoked", message="Refresh token revoked")
        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise AppException(status_code=401, code="refresh_expired", message="Refresh token expired")

        self.refresh_repo.revoke(token, revoked_at=datetime.now(timezone.utc))

        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise AppException(status_code=404, code="user_not_found", message="User not found")
        return self._build_auth_response(user)

    def logout(self, payload: LogoutRequest) -> dict[str, str]:
        claims = decode_token(payload.refresh_token)
        if claims.get("type") != "refresh":
            raise AppException(status_code=401, code="invalid_token_type", message="Not a refresh token")

        jti = claims.get("jti")
        if jti:
            token = self.refresh_repo.get_by_jti(jti)
            if token and token.revoked_at is None:
                self.refresh_repo.revoke(token, revoked_at=datetime.now(timezone.utc))
                self.db.commit()

        return {"message": "Logged out successfully"}

    def request_password_reset(self, payload: PasswordResetRequest) -> PasswordResetRequestResponse:
        generic_message = "If the email exists, a password reset link has been sent"
        user = self.user_repo.get_by_email(payload.email)
        if user is None:
            return PasswordResetRequestResponse(message=generic_message)

        mail_service = MailService(self.settings)
        if not mail_service.is_configured and self.settings.app_env != "development":
            raise AppException(status_code=503, code="mail_not_configured", message="Password reset email is not configured")

        now = datetime.now(timezone.utc)
        latest_token = self.password_reset_repo.get_latest_for_user(user_id=user.id)
        if latest_token is not None:
            latest_created_at = latest_token.created_at
            if latest_created_at.tzinfo is None:
                latest_created_at = latest_created_at.replace(tzinfo=timezone.utc)
            if now - latest_created_at < timedelta(seconds=PASSWORD_RESET_REQUEST_COOLDOWN_SECONDS):
                return PasswordResetRequestResponse(message=generic_message)

        raw_token = secrets.token_urlsafe(32)
        token_hash = _hash_reset_token(raw_token)
        expires_at = now + timedelta(
            minutes=self.settings.password_reset_token_expire_minutes,
        )
        self.password_reset_repo.mark_pending_used_for_user(user_id=user.id, used_at=now)
        self.password_reset_repo.create(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        self.db.commit()

        reset_url = f"{self.settings.password_reset_url}?{urlencode({'reset_token': raw_token})}"
        mail_service.send_password_reset(to_email=user.email, reset_url=reset_url)

        dev_reset_token = raw_token if self.settings.app_env == "development" and not mail_service.is_configured else None
        return PasswordResetRequestResponse(message=generic_message, dev_reset_token=dev_reset_token)

    def reset_password(self, payload: PasswordResetConfirmRequest) -> dict[str, str]:
        token_hash = _hash_reset_token(payload.token)
        token = self.password_reset_repo.get_by_hash(token_hash)
        now = datetime.now(timezone.utc)
        if token is None or token.used_at is not None:
            raise AppException(status_code=400, code="invalid_reset_token", message="Invalid or expired reset token")

        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise AppException(status_code=400, code="invalid_reset_token", message="Invalid or expired reset token")

        token.user.password_hash = hash_password(payload.password)
        self.password_reset_repo.mark_used(token, used_at=now)
        self.db.add(token.user)
        self.db.commit()
        return {"message": "Password reset successfully"}


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
