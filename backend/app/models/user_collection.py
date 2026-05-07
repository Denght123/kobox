import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CollectionStatus(str, enum.Enum):
    completed = "completed"
    watching = "watching"
    plan_to_watch = "plan_to_watch"
    on_hold = "on_hold"
    dropped = "dropped"


class UserCollection(Base):
    __tablename__ = "user_collections"
    __table_args__ = (UniqueConstraint("user_id", "anime_id", name="uq_user_collection_anime"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    anime_id: Mapped[int] = mapped_column(Integer, ForeignKey("anime.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_status: Mapped[CollectionStatus] = mapped_column(
        Enum(CollectionStatus, name="collection_status_enum"),
        nullable=False,
        default=CollectionStatus.plan_to_watch,
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="collections")
    anime = relationship("Anime", back_populates="collections")
