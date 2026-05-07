from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: int, token_jti: str, expires_at: datetime) -> RefreshToken:
        item = RefreshToken(user_id=user_id, token_jti=token_jti, expires_at=expires_at)
        self.db.add(item)
        self.db.flush()
        return item

    def get_by_jti(self, token_jti: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_jti == token_jti)
        return self.db.scalars(stmt).first()

    def revoke(self, token: RefreshToken, revoked_at: datetime) -> RefreshToken:
        token.revoked_at = revoked_at
        self.db.add(token)
        self.db.flush()
        return token
