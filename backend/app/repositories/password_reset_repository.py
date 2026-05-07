from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.models.password_reset_token import PasswordResetToken
from app.models.user import User


class PasswordResetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: int, token_hash: str, expires_at: datetime) -> PasswordResetToken:
        item = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(item)
        self.db.flush()
        return item

    def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        stmt = (
            select(PasswordResetToken)
            .options(joinedload(PasswordResetToken.user).joinedload(User.profile))
            .where(PasswordResetToken.token_hash == token_hash)
        )
        return self.db.scalars(stmt).first()

    def get_latest_for_user(self, *, user_id: int) -> PasswordResetToken | None:
        stmt = (
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id)
            .order_by(PasswordResetToken.created_at.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def mark_pending_used_for_user(self, *, user_id: int, used_at: datetime) -> None:
        self.db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=used_at),
        )
        self.db.flush()

    def mark_used(self, token: PasswordResetToken, used_at: datetime) -> None:
        token.used_at = used_at
        self.db.add(token)
        self.db.flush()
