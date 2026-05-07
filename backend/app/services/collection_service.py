from sqlalchemy.orm import Session
from typing import cast

from app.core.response_cache import get_cached, invalidate_cache_prefix, set_cached
from app.core.exceptions import AppException
from app.models.user import User
from app.models.user_collection import CollectionStatus
from app.repositories.anime_repository import AnimeRepository
from app.repositories.collection_repository import CollectionRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.schemas.collection import CollectionCreateRequest, CollectionItem, CollectionUpdateRequest
from app.schemas.common import PaginatedResponse
from app.services.anime_service import AnimeService
from app.services.anime_mapper import map_anime

CACHE_TTL_SECONDS = 60


class CollectionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.collection_repo = CollectionRepository(db)
        self.anime_repo = AnimeRepository(db)
        self.favorite_repo = FavoriteRepository(db)

    def list_collections(
        self,
        *,
        user: User | None = None,
        user_id: int | None = None,
        page: int,
        page_size: int,
        status: CollectionStatus | None,
        language_code: str,
        include_total: bool = True,
    ) -> PaginatedResponse:
        resolved_user_id = user_id if user_id is not None else user.id if user is not None else None
        if resolved_user_id is None:
            raise AppException(status_code=401, code="missing_user", message="User is required")
        cache_key = (
            f"collections:{resolved_user_id}:{language_code}:{status.value if status else 'all'}:"
            f"{page}:{page_size}:{int(include_total)}"
        )
        cached = cast(PaginatedResponse | None, get_cached(cache_key, ttl_seconds=CACHE_TTL_SECONDS))
        if cached is not None:
            return cached

        items, total = self.collection_repo.list_by_user(
            user_id=resolved_user_id,
            page=page,
            page_size=page_size,
            status=status,
            include_total=include_total,
        )
        seen_anime_ids: set[int] = set()
        result: list[CollectionItem] = []
        for item in items:
            if item.anime_id in seen_anime_ids:
                continue
            seen_anime_ids.add(item.anime_id)
            result.append(
                CollectionItem(
                    id=item.id,
                    user_id=item.user_id,
                    collection_status=item.collection_status,
                    added_at=item.added_at,
                    updated_at=item.updated_at,
                    anime=map_anime(item.anime, language_code=language_code),
                )
            )
        response = PaginatedResponse(
            items=result,
            total=total if include_total else len(result),
            page=page,
            page_size=page_size,
        )
        set_cached(cache_key, response)
        return response

    def add_collection(self, *, user: User, payload: CollectionCreateRequest, language_code: str) -> CollectionItem:
        anime = self.anime_repo.get_by_id(payload.anime_id) if is_persisted_anime_id(payload.anime_id) else None
        if anime is None and payload.source_id:
            anime = self.anime_repo.get_by_source_id(payload.source_id)
        if anime is None and payload.source_id:
            try:
                anime = AnimeService(self.db).ensure_anime_by_source_id(payload.source_id)
            except LookupError:
                anime = None
        if anime is None:
            raise AppException(status_code=404, code="anime_not_found", message="Anime not found")

        existing = self.collection_repo.get_by_user_anime(user_id=user.id, anime_id=anime.id)
        if existing:
            existing.collection_status = payload.collection_status
            self.db.add(existing)
            self.db.commit()
            invalidate_user_collection_cache(user.id)
            refreshed = self.collection_repo.get_by_id_for_user(user_id=user.id, collection_id=existing.id)
            assert refreshed is not None
            return CollectionItem(
                id=refreshed.id,
                user_id=refreshed.user_id,
                collection_status=refreshed.collection_status,
                added_at=refreshed.added_at,
                updated_at=refreshed.updated_at,
                anime=map_anime(refreshed.anime, language_code=language_code),
            )

        created = self.collection_repo.create(
            user_id=user.id, anime_id=anime.id, status=payload.collection_status
        )
        self.db.commit()
        invalidate_user_collection_cache(user.id)
        created_item = self.collection_repo.get_by_id_for_user(user_id=user.id, collection_id=created.id)
        assert created_item is not None
        return CollectionItem(
            id=created_item.id,
            user_id=created_item.user_id,
            collection_status=created_item.collection_status,
            added_at=created_item.added_at,
            updated_at=created_item.updated_at,
            anime=map_anime(created_item.anime, language_code=language_code),
        )

    def update_collection(
        self,
        *,
        user: User,
        collection_id: int,
        payload: CollectionUpdateRequest,
        language_code: str,
    ) -> CollectionItem:
        item = self.collection_repo.get_by_id_for_user(user_id=user.id, collection_id=collection_id)
        if item is None:
            raise AppException(status_code=404, code="collection_not_found", message="Collection not found")

        item.collection_status = payload.collection_status
        self.db.add(item)
        self.db.commit()
        invalidate_user_collection_cache(user.id)
        self.db.refresh(item)
        return CollectionItem(
            id=item.id,
            user_id=item.user_id,
            collection_status=item.collection_status,
            added_at=item.added_at,
            updated_at=item.updated_at,
            anime=map_anime(item.anime, language_code=language_code),
        )

    def delete_collection(self, *, user: User, collection_id: int) -> dict[str, str]:
        item = self.collection_repo.get_by_id_for_user(user_id=user.id, collection_id=collection_id)
        if item is None:
            raise AppException(status_code=404, code="collection_not_found", message="Collection not found")
        anime_id = item.anime_id
        self.collection_repo.delete(item)
        self.favorite_repo.delete_by_user_anime(user_id=user.id, anime_id=anime_id)
        self.db.commit()
        invalidate_user_collection_cache(user.id)
        invalidate_user_favorite_cache(user.id)
        return {"message": "Collection deleted"}


def is_persisted_anime_id(anime_id: int | None) -> bool:
    return anime_id is not None and 0 < anime_id <= 2_147_483_647


def invalidate_user_collection_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"collections:{user_id}:")
    invalidate_cache_prefix(f"dashboard:{user_id}:")


def invalidate_user_favorite_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"favorites:{user_id}:")
    invalidate_cache_prefix(f"dashboard:{user_id}:")
