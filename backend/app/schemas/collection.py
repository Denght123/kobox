from datetime import datetime

from pydantic import BaseModel, model_validator

from app.models.user_collection import CollectionStatus
from app.schemas.anime import AnimeItem


class CollectionCreateRequest(BaseModel):
    anime_id: int | None = None
    source_id: str | None = None
    collection_status: CollectionStatus = CollectionStatus.plan_to_watch

    @model_validator(mode="after")
    def _validate_target(self) -> "CollectionCreateRequest":
        if self.anime_id is None and not self.source_id:
            raise ValueError("anime_id or source_id is required")
        return self


class CollectionUpdateRequest(BaseModel):
    collection_status: CollectionStatus


class CollectionItem(BaseModel):
    id: int
    user_id: int
    collection_status: CollectionStatus
    added_at: datetime
    updated_at: datetime
    anime: AnimeItem
