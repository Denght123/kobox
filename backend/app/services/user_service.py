from pathlib import Path
from typing import cast
from urllib.parse import urljoin
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.response_cache import get_cached, invalidate_cache_prefix, set_cached
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    AvatarUploadResponse,
    BackgroundUploadResponse,
    UserDashboardResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserSettingsResponse,
    UserSettingsUpdateRequest,
)
from app.services.collection_service import CollectionService
from app.services.favorite_service import FavoriteService

CACHE_TTL_SECONDS = 60


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.settings = get_settings()

    def _build_profile_response(self, user: User) -> UserProfileResponse:
        return UserProfileResponse(
            id=user.id,
            username=user.username,
            public_slug=user.profile.public_slug,
            display_name=user.profile.display_name,
            avatar_url=user.profile.avatar_url,
            background_image_url=user.profile.background_image_url,
            birthday=user.profile.birthday,
            bio=user.profile.bio,
            is_public=user.profile.is_public,
        )

    def get_me(self, user: User) -> UserProfileResponse:
        return self._build_profile_response(user)

    def update_profile(self, user: User, payload: UserProfileUpdateRequest) -> UserProfileResponse:
        updated = self.user_repo.update_profile(
            user=user,
            avatar_url=payload.avatar_url,
            background_image_url=payload.background_image_url,
            display_name=payload.display_name,
            birthday=payload.birthday,
            bio=payload.bio,
            is_public=payload.is_public,
        )
        self.db.commit()
        invalidate_user_dashboard_cache(user.id)
        refreshed = self.user_repo.get_by_id(updated.id)
        if refreshed is None:
            raise AppException(status_code=404, code="user_not_found", message="User not found")
        return self._build_profile_response(refreshed)

    def get_settings(self, user: User) -> UserSettingsResponse:
        profile = user.profile
        return UserSettingsResponse(
            language=profile.language,
            show_dynamic_background=profile.show_dynamic_background,
            show_public_rank=profile.show_public_rank,
        )

    def get_dashboard(self, user: User, *, language_code: str) -> UserDashboardResponse:
        response = self._build_dashboard_response(user, language_code=language_code)
        set_cached(f"dashboard:{user.id}:{language_code}", response)
        return response

    def get_dashboard_by_user_id(self, user_id: int, *, language_code: str) -> UserDashboardResponse:
        cache_key = f"dashboard:{user_id}:{language_code}"
        cached = cast(UserDashboardResponse | None, get_cached(cache_key, ttl_seconds=CACHE_TTL_SECONDS))
        if cached is not None:
            return cached

        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise AppException(status_code=401, code="user_not_found", message="User not found")
        if not user.is_active:
            raise AppException(status_code=403, code="inactive_user", message="User is inactive")
        return self.get_dashboard(user, language_code=language_code)

    def _build_dashboard_response(self, user: User, *, language_code: str) -> UserDashboardResponse:
        return UserDashboardResponse(
            profile=self.get_me(user),
            settings=self.get_settings(user),
            collections=CollectionService(self.db).list_collections(
                user=user,
                page=1,
                page_size=100,
                status=None,
                language_code=language_code,
                include_total=False,
            ),
            favorites=FavoriteService(self.db).list_favorites(user=user, language_code=language_code),
        )

    def update_settings(
        self,
        user: User,
        payload: UserSettingsUpdateRequest,
    ) -> UserSettingsResponse:
        updated = self.user_repo.update_settings(
            user=user,
            language=payload.language,
            show_dynamic_background=payload.show_dynamic_background,
            show_public_rank=payload.show_public_rank,
        )
        self.db.commit()
        invalidate_user_dashboard_cache(user.id)
        refreshed = self.user_repo.get_by_id(updated.id)
        if refreshed is None:
            raise AppException(status_code=404, code="user_not_found", message="User not found")
        return self.get_settings(refreshed)

    async def upload_avatar(self, *, user: User, file: UploadFile, request_base_url: str) -> AvatarUploadResponse:
        image_url = await self._store_uploaded_image(
            user=user,
            file=file,
            request_base_url=request_base_url,
            folder="avatars",
            filename_prefix="avatar",
            error_label="Avatar",
        )
        updated = self.user_repo.update_profile(user=user, avatar_url=image_url)
        self.db.commit()
        invalidate_user_dashboard_cache(user.id)
        refreshed = self.user_repo.get_by_id(updated.id)
        if refreshed is None:
            raise AppException(status_code=404, code="user_not_found", message="User not found")
        return AvatarUploadResponse(avatar_url=image_url, profile=self._build_profile_response(refreshed))

    async def upload_background(
        self,
        *,
        user: User,
        file: UploadFile,
        request_base_url: str,
    ) -> BackgroundUploadResponse:
        image_url = await self._store_uploaded_image(
            user=user,
            file=file,
            request_base_url=request_base_url,
            folder="backgrounds",
            filename_prefix="background",
            error_label="Background image",
        )
        updated = self.user_repo.update_profile(user=user, background_image_url=image_url)
        self.db.commit()
        invalidate_user_dashboard_cache(user.id)
        refreshed = self.user_repo.get_by_id(updated.id)
        if refreshed is None:
            raise AppException(status_code=404, code="user_not_found", message="User not found")
        return BackgroundUploadResponse(
            background_image_url=image_url,
            profile=self._build_profile_response(refreshed),
        )

    def clear_background(self, user: User) -> BackgroundUploadResponse:
        updated = self.user_repo.clear_background_image(user=user)
        self.db.commit()
        invalidate_user_dashboard_cache(user.id)
        refreshed = self.user_repo.get_by_id(updated.id)
        if refreshed is None:
            raise AppException(status_code=404, code="user_not_found", message="User not found")
        return BackgroundUploadResponse(
            background_image_url="",
            profile=self._build_profile_response(refreshed),
        )

    async def _store_uploaded_image(
        self,
        *,
        user: User,
        file: UploadFile,
        request_base_url: str,
        folder: str,
        filename_prefix: str,
        error_label: str,
    ) -> str:
        try:
            content_type = (file.content_type or "").lower()
            allowed_types = self.settings.upload_allowed_image_types_list
            if content_type not in allowed_types:
                raise AppException(
                    status_code=400,
                    code="unsupported_image_type",
                    message=f"{error_label} file type is not supported",
                    details={"allowed_types": allowed_types},
                )

            raw = await file.read()
            if not raw:
                raise AppException(status_code=400, code="empty_file", message=f"{error_label} file is empty")
            if len(raw) > self.settings.upload_max_bytes:
                raise AppException(
                    status_code=413,
                    code="file_too_large",
                    message=f"{error_label} file exceeds max size limit",
                    details={"max_bytes": self.settings.upload_max_bytes},
                )

            ext = self._resolve_extension(content_type=content_type, filename=file.filename)
            upload_dir = self.settings.uploads_path / folder
            upload_dir.mkdir(parents=True, exist_ok=True)
            filename = f"user-{user.id}-{filename_prefix}-{uuid4().hex}{ext}"
            output_path = upload_dir / filename
            output_path.write_bytes(raw)

            relative_url = f"{self.settings.uploads_url_prefix}/{folder}/{filename}"
            return urljoin(f"{request_base_url.rstrip('/')}/", relative_url.lstrip("/"))
        finally:
            await file.close()

    @staticmethod
    def _resolve_extension(content_type: str, filename: str | None) -> str:
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }
        if content_type in ext_map:
            return ext_map[content_type]
        if filename:
            suffix = Path(filename).suffix.lower()
            if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                return ".jpg" if suffix == ".jpeg" else suffix
        return ".bin"


def invalidate_user_dashboard_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"dashboard:{user_id}:")
