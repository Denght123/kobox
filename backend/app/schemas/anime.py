from pydantic import BaseModel, ConfigDict, Field


class AnimeTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language_code: str
    title: str
    summary: str | None = None


class AnimeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: str | None = None
    cover_url: str
    source_cover_url: str | None = None
    local_cover_url: str | None = None
    year: int | None = None
    season: str | None = None
    status: str
    title: str
    summary: str | None = None
    genres: list[str] = Field(default_factory=list)


class AnimeSuggestionItem(BaseModel):
    id: int
    title: str
