from datetime import date

from pydantic import BaseModel, Field

from app.schemas.collection import CollectionItem
from app.schemas.common import PaginatedResponse
from app.schemas.favorite import FavoriteItem


class UserProfileResponse(BaseModel):
    id: int
    username: str
    public_slug: str
    display_name: str
    avatar_url: str | None = None
    background_image_url: str | None = None
    birthday: date | None = None
    bio: str | None = None
    is_public: bool


class UserProfileUpdateRequest(BaseModel):
    avatar_url: str | None = Field(default=None, max_length=500)
    background_image_url: str | None = Field(default=None, max_length=500)
    display_name: str | None = Field(default=None, max_length=128)
    birthday: date | None = None
    bio: str | None = Field(default=None, max_length=1000)
    is_public: bool | None = None


class UserSettingsResponse(BaseModel):
    language: str
    show_dynamic_background: bool
    show_public_rank: bool


class UserSettingsUpdateRequest(BaseModel):
    language: str | None = Field(default=None, max_length=16)
    show_dynamic_background: bool | None = None
    show_public_rank: bool | None = None


class AvatarUploadResponse(BaseModel):
    avatar_url: str
    profile: UserProfileResponse


class BackgroundUploadResponse(BaseModel):
    background_image_url: str
    profile: UserProfileResponse


class UserDashboardResponse(BaseModel):
    profile: UserProfileResponse
    settings: UserSettingsResponse
    collections: PaginatedResponse[CollectionItem]
    favorites: PaginatedResponse[FavoriteItem]
