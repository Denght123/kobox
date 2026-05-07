from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.user_collection import CollectionStatus, UserCollection
from app.repositories.collection_repository import CollectionRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.favorite import FavoriteItem
from app.schemas.public import PublicUserProfileResponse
from app.services.anime_mapper import map_anime
from app.schemas.collection import CollectionItem


class PublicService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.collection_repo = CollectionRepository(db)
        self.favorite_repo = FavoriteRepository(db)

    def _get_public_user(self, username: str):
        user = self.user_repo.get_by_public_slug(username)
        if user is None:
            raise AppException(status_code=404, code="user_not_found", message="Public user not found")
        if not user.profile or not user.profile.is_public:
            raise AppException(status_code=404, code="profile_private", message="Public profile is private")
        return user

    def profile(self, *, username: str) -> PublicUserProfileResponse:
        user = self._get_public_user(username)
        count_stmt = select(func.count(UserCollection.id)).where(UserCollection.user_id == user.id)
        collection_count = self.db.scalar(count_stmt) or 0
        return PublicUserProfileResponse(
            id=user.id,
            username=user.profile.public_slug,
            public_slug=user.profile.public_slug,
            display_name=user.profile.display_name,
            avatar_url=user.profile.avatar_url,
            background_image_url=user.profile.background_image_url,
            birthday=user.profile.birthday,
            bio=user.profile.bio,
            is_public=user.profile.is_public,
            collection_count=collection_count,
        )

    def collections(
        self,
        *,
        username: str,
        page: int,
        page_size: int,
        status: CollectionStatus | None,
        language_code: str,
    ) -> PaginatedResponse:
        user = self._get_public_user(username)
        rows, total = self.collection_repo.list_by_user(
            user_id=user.id,
            page=page,
            page_size=page_size,
            status=status,
        )
        items = [
            CollectionItem(
                id=row.id,
                user_id=row.user_id,
                collection_status=row.collection_status,
                added_at=row.added_at,
                updated_at=row.updated_at,
                anime=map_anime(row.anime, language_code=language_code),
            )
            for row in rows
        ]
        return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)

    def favorites(self, *, username: str, language_code: str) -> PaginatedResponse:
        user = self._get_public_user(username)
        if not user.profile.show_public_rank:
            return PaginatedResponse(items=[], total=0, page=1, page_size=10)
        rows = self.favorite_repo.list_by_user(user_id=user.id)
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
        return PaginatedResponse(items=items, total=len(items), page=1, page_size=len(items) if items else 10)
