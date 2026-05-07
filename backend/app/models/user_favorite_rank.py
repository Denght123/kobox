from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.model_mixins import TimestampMixin


class UserFavoriteRank(Base, TimestampMixin):
    __tablename__ = "user_favorite_ranks"
    __table_args__ = (
        UniqueConstraint("user_id", "anime_id", name="uq_user_favorite_anime"),
        UniqueConstraint("user_id", "rank_order", name="uq_user_favorite_rank_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    anime_id: Mapped[int] = mapped_column(Integer, ForeignKey("anime.id", ondelete="CASCADE"), nullable=False, index=True)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    user = relationship("User", back_populates="favorite_ranks")
    anime = relationship("Anime", back_populates="favorite_ranks")

