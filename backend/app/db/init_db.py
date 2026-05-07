from datetime import datetime, timedelta, timezone
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_refresh_token, hash_password
from app.models.anime import Anime, AnimeTranslation
from app.models.user import User
from app.models.user_collection import CollectionStatus, UserCollection
from app.models.user_favorite_rank import UserFavoriteRank
from app.models.user_profile import UserProfile
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.db.anime_seed_data import SEED_ANIME_ITEMS


def _seed_anime(db: Session) -> list[Anime]:
    existing = db.scalars(select(Anime).limit(1)).first()
    if existing is not None:
        return list(db.scalars(select(Anime)).all())

    anime_rows: list[Anime] = []
    for item in SEED_ANIME_ITEMS:
        anime = Anime(
            source_id=item["source_id"],
            cover_url=item["cover_url"],
            source_cover_url=item["cover_url"],
            local_cover_url=None,
            cover_source="bangumi",
            is_adult=False,
            year=item["year"],
            season=item["season"],
            status=item["status"],
            genres_json=json.dumps(item.get("genres", [])),
        )
        for language_code, title, summary in item["translations"]:
            anime.translations.append(
                AnimeTranslation(language_code=language_code, title=title, summary=summary)
            )
        db.add(anime)
        anime_rows.append(anime)

    db.flush()
    return anime_rows


def _seed_demo_user(db: Session, anime_rows: list[Anime]) -> None:
    existing = db.scalars(select(User).where(User.email == "demo@kobox.local")).first()
    if existing is not None:
        return

    user = User(
        email="demo@kobox.local",
        username="demo",
        password_hash=hash_password("Demo1234!"),
        is_active=True,
    )
    user.profile = UserProfile(
        display_name="Kobox Demo",
        public_slug="demo",
        bio="Demo profile for frontend integration.",
        is_public=True,
    )
    db.add(user)
    db.flush()

    if anime_rows:
        db.add(
            UserCollection(
                user_id=user.id,
                anime_id=anime_rows[0].id,
                collection_status=CollectionStatus.completed,
            )
        )
        db.add(
            UserCollection(
                user_id=user.id,
                anime_id=anime_rows[1].id,
                collection_status=CollectionStatus.completed,
            )
        )
        db.add(
            UserCollection(
                user_id=user.id,
                anime_id=anime_rows[2].id,
                collection_status=CollectionStatus.watching,
            )
        )
        db.add(
            UserCollection(
                user_id=user.id,
                anime_id=anime_rows[3].id,
                collection_status=CollectionStatus.plan_to_watch,
            )
        )
        db.flush()

        db.add(UserFavoriteRank(user_id=user.id, anime_id=anime_rows[0].id, rank_order=1))
        db.add(UserFavoriteRank(user_id=user.id, anime_id=anime_rows[1].id, rank_order=2))
        db.add(UserFavoriteRank(user_id=user.id, anime_id=anime_rows[2].id, rank_order=3))

    # Add one refresh token for quick manual API testing.
    settings = get_settings()
    _, jti = create_refresh_token(user_id=user.id, username=user.username)
    RefreshTokenRepository(db).create(
        user_id=user.id,
        token_jti=jti,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )


def seed_data(db: Session) -> None:
    anime_rows = _seed_anime(db)
    _seed_demo_user(db, anime_rows)
    db.commit()
