from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

import httpx

from app.core.config import get_settings

SEARCH_CACHE_TTL_SECONDS = 600.0


@dataclass(slots=True)
class KitsuCacheEntry:
    expires_at: float
    items: list["KitsuAnime"]


@dataclass(slots=True)
class KitsuAnime:
    source_id: str
    title_canonical: str
    title_english: str | None
    title_japanese: str | None
    title_romaji: str | None
    title_synonyms: list[str]
    summary: str | None
    cover_url: str
    source_cover_url: str | None
    year: int | None
    season: str | None
    status: str
    is_adult: bool
    popularity: int


class KitsuClient:
    _search_cache: dict[tuple[str, int, int], KitsuCacheEntry] = {}

    def __init__(self) -> None:
        self.settings = get_settings()
        self._base_url = self.settings.kitsu_api_url.rstrip("/")

    def search(self, *, query: str, page: int, page_size: int) -> list[KitsuAnime]:
        cache_key = (query.strip().casefold(), page, page_size)
        cached = self._search_cache.get(cache_key)
        now = monotonic()
        if cached and cached.expires_at > now:
            return list(cached.items)

        with httpx.Client(timeout=self.settings.kitsu_timeout_seconds, trust_env=False) as client:
            response = client.get(
                f"{self._base_url}/anime",
                params={
                    "filter[text]": query,
                    "page[limit]": page_size,
                    "page[offset]": max(page - 1, 0) * page_size,
                },
            )
            response.raise_for_status()
            body = response.json()

        rows = body.get("data", [])
        if not isinstance(rows, list):
            return []

        result: list[KitsuAnime] = []
        for row in rows:
            anime = self._map_row(row)
            if anime is not None:
                result.append(anime)

        self._search_cache[cache_key] = KitsuCacheEntry(
            expires_at=now + SEARCH_CACHE_TTL_SECONDS,
            items=list(result),
        )
        return result

    def get_anime(self, kitsu_id: str) -> KitsuAnime | None:
        with httpx.Client(timeout=self.settings.kitsu_timeout_seconds, trust_env=False) as client:
            response = client.get(f"{self._base_url}/anime/{kitsu_id}")
            response.raise_for_status()
            body = response.json()
        row = body.get("data")
        return self._map_row(row) if isinstance(row, dict) else None

    def _map_row(self, row: dict) -> KitsuAnime | None:
        if not isinstance(row, dict):
            return None

        kitsu_id = row.get("id")
        if not kitsu_id:
            return None

        attributes = row.get("attributes")
        if not isinstance(attributes, dict):
            return None

        titles = attributes.get("titles") if isinstance(attributes.get("titles"), dict) else {}
        canonical_title = self._clean_text(attributes.get("canonicalTitle"))
        english = self._clean_text(titles.get("en")) or self._clean_text(attributes.get("titles", {}).get("en_us"))
        japanese = self._clean_text(titles.get("ja_jp"))
        romaji = self._clean_text(titles.get("en_jp"))
        if not (canonical_title or english or japanese or romaji):
            return None

        poster = attributes.get("posterImage") if isinstance(attributes.get("posterImage"), dict) else {}
        cover_url = (
            self._clean_text(poster.get("original"))
            or self._clean_text(poster.get("large"))
            or self._clean_text(poster.get("medium"))
        )
        if not cover_url:
            return None

        title_synonyms = [
            cleaned
            for raw in attributes.get("abbreviatedTitles", [])
            for cleaned in [self._clean_text(raw)]
            if cleaned
        ]

        start_date = self._clean_text(attributes.get("startDate"))
        year = None
        if start_date and len(start_date) >= 4 and start_date[:4].isdigit():
            year = int(start_date[:4])

        return KitsuAnime(
            source_id=f"kitsu:{kitsu_id}",
            title_canonical=canonical_title or romaji or english or japanese or f"Anime {kitsu_id}",
            title_english=english,
            title_japanese=japanese,
            title_romaji=romaji,
            title_synonyms=title_synonyms,
            summary=self._clean_text(attributes.get("synopsis")),
            cover_url=cover_url,
            source_cover_url=cover_url,
            year=year,
            season=None,
            status=self._map_status(self._clean_text(attributes.get("status"))),
            is_adult=bool(attributes.get("nsfw")),
            popularity=self._popularity_score(attributes),
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
        if normalized in {"finished", "completed"}:
            return "finished"
        if normalized in {"current", "airing"}:
            return "airing"
        if normalized in {"upcoming", "tba", "unreleased"}:
            return "upcoming"
        return "unknown"

    @staticmethod
    def _popularity_score(attributes: dict) -> int:
        user_count = attributes.get("userCount")
        favorites_count = attributes.get("favoritesCount")
        average_rating = KitsuClient._clean_text(attributes.get("averageRating"))
        try:
            rating_score = int(float(average_rating or "0") * 100)
        except ValueError:
            rating_score = 0
        return (
            (user_count if isinstance(user_count, int) else 0)
            + (favorites_count if isinstance(favorites_count, int) else 0) * 5
            + rating_score
        )
