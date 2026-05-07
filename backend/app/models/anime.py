from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.model_mixins import TimestampMixin


class Anime(Base, TimestampMixin):
    __tablename__ = "anime"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    cover_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_source: Mapped[str] = mapped_column(String(64), nullable=False, default="seed")
    is_adult: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    season: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="finished")
    genres_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    translations = relationship("AnimeTranslation", back_populates="anime", cascade="all, delete-orphan")
    collections = relationship("UserCollection", back_populates="anime")
    favorite_ranks = relationship("UserFavoriteRank", back_populates="anime")


class AnimeTranslation(Base):
    __tablename__ = "anime_translations"
    __table_args__ = (UniqueConstraint("anime_id", "language_code", name="uq_anime_language"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anime_id: Mapped[int] = mapped_column(Integer, ForeignKey("anime.id", ondelete="CASCADE"), nullable=False, index=True)
    language_code: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    anime = relationship("Anime", back_populates="translations")
