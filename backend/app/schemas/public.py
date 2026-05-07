from datetime import date

from pydantic import BaseModel

from app.schemas.anime import AnimeItem


class PublicUserProfileResponse(BaseModel):
    id: int
    username: str
    public_slug: str
    display_name: str
    avatar_url: str | None = None
    background_image_url: str | None = None
    birthday: date | None = None
    bio: str | None = None
    is_public: bool
    collection_count: int


class PublicFavoriteItem(BaseModel):
    rank_order: int
    anime: AnimeItem
