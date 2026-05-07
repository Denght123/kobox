from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

import httpx

from app.core.config import get_settings

SEARCH_CACHE_TTL_SECONDS = 600.0


@dataclass(slots=True)
class JikanCacheEntry:
    expires_at: float
    items: list["JikanAnime"]


@dataclass(slots=True)
class JikanAnime:
    source_id: str
    title_default: str
    title_english: str | None
    title_japanese: str | None
    title_synonyms: list[str]
    summary: str | None
    genres: list[str]
    cover_url: str
    source_cover_url: str | None
    year: int | None
    season: str | None
    status: str
    is_adult: bool
    popularity: int


class JikanClient:
    _search_cache: dict[tuple[str, int, int], JikanCacheEntry] = {}

    def __init__(self) -> None:
        self.settings = get_settings()
        self._base_url = self.settings.jikan_api_url.rstrip("/")

    def search(self, *, query: str, page: int, page_size: int) -> list[JikanAnime]:
        cache_key = (query.strip().casefold(), page, page_size)
        cached = self._search_cache.get(cache_key)
        now = monotonic()
        if cached and cached.expires_at > now:
            return list(cached.items)

        with httpx.Client(timeout=self.settings.jikan_timeout_seconds, trust_env=False) as client:
            response = client.get(
                f"{self._base_url}/anime",
                params={
                    "q": query,
                    "page": page,
                    "limit": page_size,
                    "sfw": "true",
                },
            )
            response.raise_for_status()
            body = response.json()

        rows = body.get("data", [])
        if not isinstance(rows, list):
            return []

        result: list[JikanAnime] = []
        for row in rows:
            anime = self._map_row(row)
            if anime is not None:
                result.append(anime)

        self._search_cache[cache_key] = JikanCacheEntry(
            expires_at=now + SEARCH_CACHE_TTL_SECONDS,
            items=list(result),
        )
        return result

    def get_anime(self, mal_id: int) -> JikanAnime | None:
        with httpx.Client(timeout=self.settings.jikan_timeout_seconds, trust_env=False) as client:
            response = client.get(f"{self._base_url}/anime/{mal_id}", params={"sfw": "true"})
            response.raise_for_status()
            body = response.json()
        row = body.get("data")
        return self._map_row(row) if isinstance(row, dict) else None

    def _map_row(self, row: dict) -> JikanAnime | None:
        if not isinstance(row, dict):
            return None

        mal_id = row.get("mal_id")
        if not mal_id:
            return None

        title_default = self._clean_text(row.get("title"))
        title_english = self._clean_text(row.get("title_english"))
        title_japanese = self._clean_text(row.get("title_japanese"))
        if not (title_default or title_english or title_japanese):
            return None

        title_synonyms = [
            cleaned
            for raw in row.get("title_synonyms", [])
            for cleaned in [self._clean_text(raw)]
            if cleaned
        ]

        titles = row.get("titles")
        if isinstance(titles, list):
            for title_item in titles:
                if not isinstance(title_item, dict):
                    continue
                title_type = str(title_item.get("type", "")).lower()
                title_value = self._clean_text(title_item.get("title"))
                if not title_value:
                    continue
                if title_type == "english" and not title_english:
                    title_english = title_value
                elif title_type == "japanese" and not title_japanese:
                    title_japanese = title_value
                elif title_type == "synonym" and title_value not in title_synonyms:
                    title_synonyms.append(title_value)

        image_block = row.get("images") or {}
        jpg = image_block.get("jpg") if isinstance(image_block, dict) else {}
        webp = image_block.get("webp") if isinstance(image_block, dict) else {}
        cover_url = (
            self._clean_text((jpg or {}).get("large_image_url"))
            or self._clean_text((webp or {}).get("large_image_url"))
            or self._clean_text((jpg or {}).get("image_url"))
            or self._clean_text((webp or {}).get("image_url"))
        )
        if not cover_url:
            return None

        explicit_genres = row.get("explicit_genres")
        rating = self._clean_text(row.get("rating"))
        is_adult = bool(explicit_genres) or bool(rating and rating.startswith("Rx"))

        genres = []
        for collection_name in ("genres", "themes", "demographics"):
            entries = row.get(collection_name)
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                genre_name = self._clean_text(entry.get("name"))
                if genre_name and genre_name not in genres:
                    genres.append(genre_name)

        season = self._clean_text(row.get("season"))
        season = season.lower() if season else None
        year = row.get("year") if isinstance(row.get("year"), int) else None

        return JikanAnime(
            source_id=f"jikan:{mal_id}",
            title_default=title_default or title_english or title_japanese or f"Anime {mal_id}",
            title_english=title_english,
            title_japanese=title_japanese,
            title_synonyms=title_synonyms,
            summary=self._clean_text(row.get("synopsis")),
            genres=genres,
            cover_url=cover_url,
            source_cover_url=cover_url,
            year=year,
            season=season,
            status=self._map_status(self._clean_text(row.get("status"))),
            is_adult=is_adult,
            popularity=self._popularity_score(row),
        )

    @staticmethod
    def _clean_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _map_status(raw_status: str | None) -> str:
        normalized = (raw_status or "").casefold()
        if normalized in {"finished airing", "finished"}:
            return "finished"
        if normalized in {"currently airing"}:
            return "airing"
        if normalized in {"not yet aired"}:
            return "upcoming"
        return "unknown"

    @staticmethod
    def _popularity_score(row: dict) -> int:
        members = row.get("members")
        favorites = row.get("favorites")
        score = row.get("score")
        return (
            (members if isinstance(members, int) else 0)
            + (favorites if isinstance(favorites, int) else 0) * 5
            + int((score if isinstance(score, (int, float)) else 0) * 1000)
        )
