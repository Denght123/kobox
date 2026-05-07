import json

from app.models.anime import Anime
from app.schemas.anime import AnimeItem


def map_anime(anime: Anime, language_code: str = "zh-CN") -> AnimeItem:
    preferred = None
    zh_fallback = None
    native_fallback = None
    en_fallback = None
    for trans in anime.translations:
        if trans.language_code == language_code:
            preferred = trans
            break
        if trans.language_code == "zh-CN" and zh_fallback is None:
            zh_fallback = trans
        elif trans.language_code == "ja" and native_fallback is None:
            native_fallback = trans
        elif trans.language_code == "en" and en_fallback is None:
            en_fallback = trans

    trans = preferred or zh_fallback or native_fallback or en_fallback or (
        anime.translations[0] if anime.translations else None
    )
    title = trans.title if trans else f"Anime #{anime.id}"
    summary = trans.summary if trans else None
    genres = _parse_genres(anime.genres_json)
    return AnimeItem(
        id=anime.id,
        source_id=anime.source_id,
        cover_url=anime.cover_url,
        source_cover_url=anime.source_cover_url,
        local_cover_url=anime.local_cover_url,
        year=anime.year,
        season=anime.season,
        status=anime.status,
        title=title,
        summary=summary,
        genres=genres,
    )


def _parse_genres(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item).strip() for item in parsed if str(item).strip()]
