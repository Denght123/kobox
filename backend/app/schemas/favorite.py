from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.anime import AnimeItem


class FavoriteItem(BaseModel):
    id: int
    user_id: int
    rank_order: int
    created_at: datetime
    updated_at: datetime
    anime: AnimeItem


class FavoriteRankInput(BaseModel):
    anime_id: int
    rank_order: int = Field(ge=1, le=100)


class FavoriteRankUpdateRequest(BaseModel):
    items: list[FavoriteRankInput]
