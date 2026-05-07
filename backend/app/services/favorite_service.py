from sqlalchemy.orm import Session
from typing import cast

from app.core.exceptions import AppException
from app.core.response_cache import get_cached, invalidate_cache_prefix, set_cached
from app.models.user import User
from app.repositories.collection_repository import CollectionRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.schemas.common import PaginatedResponse
from app.schemas.favorite import FavoriteItem, FavoriteRankUpdateRequest
from app.services.anime_mapper import map_anime

MAX_POSTGRES_INTEGER = 2_147_483_647
CACHE_TTL_SECONDS = 60


class FavoriteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.favorite_repo = FavoriteRepository(db)
        self.collection_repo = CollectionRepository(db)

    def list_favorites(self, *, user: User | None = None, user_id: int | None = None, language_code: str) -> PaginatedResponse:
        resolved_user_id = user_id if user_id is not None else user.id if user is not None else None
        if resolved_user_id is None:
            raise AppException(status_code=401, code="missing_user", message="User is required")
        cache_key = f"favorites:{resolved_user_id}:{language_code}"
        cached = cast(PaginatedResponse | None, get_cached(cache_key, ttl_seconds=CACHE_TTL_SECONDS))
        if cached is not None:
            return cached

        rows = self.favorite_repo.list_by_user(user_id=resolved_user_id)
        seen_anime_ids: set[int] = set()
        items: list[FavoriteItem] = []
        for row in rows:
            if row.anime_id in seen_anime_ids:
                continue
            seen_anime_ids.add(row.anime_id)
            items.append(
                FavoriteItem(
                    id=row.id,
                    user_id=row.user_id,
                    rank_order=len(items) + 1,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    anime=map_anime(row.anime, language_code=language_code),
                )
            )
        response = PaginatedResponse(items=items, total=len(items), page=1, page_size=len(items) if items else 10)
        set_cached(cache_key, response)
        return response

    def replace_favorites(self, *, user: User, payload: FavoriteRankUpdateRequest, language_code: str) -> PaginatedResponse:
        if len(payload.items) > 10:
            raise AppException(status_code=400, code="favorite_rank_limit", message="Favorite rank supports up to 10 items")
        seen_ranks: set[int] = set()
        seen_anime_ids: set[int] = set()
        ranks: list[tuple[int, int]] = []
        for item in payload.items:
            if item.anime_id <= 0 or item.anime_id > MAX_POSTGRES_INTEGER:
                raise AppException(status_code=400, code="invalid_anime_id", message="Invalid anime id")
            if item.rank_order in seen_ranks:
                raise AppException(status_code=400, code="duplicate_rank_order", message="Duplicate rank order")
            seen_ranks.add(item.rank_order)
            if item.anime_id in seen_anime_ids:
                raise AppException(status_code=400, code="duplicate_favorite_anime", message="Duplicate favorite anime")
            seen_anime_ids.add(item.anime_id)

            collected = self.collection_repo.get_by_user_anime(user_id=user.id, anime_id=item.anime_id)
            if collected is None:
                raise AppException(
                    status_code=400,
                    code="favorite_not_in_collection",
                    message=f"Anime {item.anime_id} is not in user collection",
                )
            ranks.append((item.anime_id, item.rank_order))

        rows = self.favorite_repo.replace_all(user_id=user.id, ranks=ranks)
        self.db.commit()
        items = [
            FavoriteItem(
                id=row.id,
                user_id=row.user_id,
                rank_order=row.rank_order,
                created_at=row.created_at,
                updated_at=row.updated_at,
                anime=map_anime(row.anime, language_code=language_code),
            )
            for row in rows
        ]
        response = PaginatedResponse(items=items, total=len(items), page=1, page_size=len(items) if items else 10)
        invalidate_user_favorite_cache(user.id)
        set_cached(f"favorites:{user.id}:{language_code}", response)
        return response


def invalidate_user_favorite_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"favorites:{user_id}:")
    invalidate_cache_prefix(f"dashboard:{user_id}:")
