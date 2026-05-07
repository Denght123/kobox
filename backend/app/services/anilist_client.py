from dataclasses import dataclass
from time import monotonic
import re

import httpx

from app.core.config import get_settings

ANILIST_SEARCH_QUERY = """
query ($search: String!, $page: Int!, $perPage: Int!) {
  Page(page: $page, perPage: $perPage) {
    media(search: $search, type: ANIME, sort: SEARCH_MATCH) {
      id
      isAdult
      season
      seasonYear
      status
      genres
      popularity
      favourites
      averageScore
      description(asHtml: false)
      coverImage {
        large
        medium
      }
      title {
        romaji
        english
        native
      }
      startDate {
        year
      }
    }
  }
}
""".strip()

ANILIST_ID_QUERY = """
query ($id: Int!) {
  Media(id: $id, type: ANIME) {
    id
    isAdult
    season
    seasonYear
    status
    genres
    popularity
    favourites
    averageScore
    description(asHtml: false)
    coverImage {
      large
      medium
    }
    title {
      romaji
      english
      native
    }
    startDate {
      year
    }
  }
}
""".strip()

SEARCH_CACHE_TTL_SECONDS = 600.0


@dataclass(slots=True)
class AniListCacheEntry:
    expires_at: float
    items: list["AniListAnime"]


@dataclass(slots=True)
class AniListAnime:
    source_id: str
    title_english: str | None
    title_native: str | None
    title_romaji: str | None
    summary: str | None
    genres: list[str]
    cover_url: str
    source_cover_url: str | None
    year: int | None
    season: str | None
    status: str
    is_adult: bool
    popularity: int


class AniListClient:
    _search_cache: dict[tuple[str, int, int], AniListCacheEntry] = {}

    def __init__(self) -> None:
        self.settings = get_settings()

    def search(self, *, query: str, page: int, page_size: int) -> list[AniListAnime]:
        cache_key = (query.strip().casefold(), page, page_size)
        cached = self._search_cache.get(cache_key)
        now = monotonic()
        if cached and cached.expires_at > now:
            return list(cached.items)

        payload = {
            "query": ANILIST_SEARCH_QUERY,
            "variables": {"search": query, "page": page, "perPage": page_size},
        }
        with httpx.Client(timeout=self.settings.anilist_timeout_seconds, trust_env=False) as client:
            response = client.post(self.settings.anilist_api_url, json=payload)
            response.raise_for_status()
            body = response.json()

        rows = body.get("data", {}).get("Page", {}).get("media", [])
        if not isinstance(rows, list):
            return []

        result: list[AniListAnime] = []
        for row in rows:
            anime = self._map_row(row)
            if anime is not None:
                result.append(anime)
        self._search_cache[cache_key] = AniListCacheEntry(
            expires_at=now + SEARCH_CACHE_TTL_SECONDS,
            items=list(result),
        )
        return result

    def get_anime(self, anilist_id: int) -> AniListAnime | None:
        payload = {
            "query": ANILIST_ID_QUERY,
            "variables": {"id": anilist_id},
        }
        with httpx.Client(timeout=self.settings.anilist_timeout_seconds, trust_env=False) as client:
            response = client.post(self.settings.anilist_api_url, json=payload)
            response.raise_for_status()
            body = response.json()
        row = body.get("data", {}).get("Media")
        return self._map_row(row) if isinstance(row, dict) else None

    def _map_row(self, row: dict) -> AniListAnime | None:
        if not isinstance(row, dict):
            return None
        row_id = row.get("id")
        if not row_id:
            return None

        titles = row.get("title") or {}
        english = self._clean_text(titles.get("english"))
        romaji = self._clean_text(titles.get("romaji"))
        native = self._clean_text(titles.get("native"))
        if not (english or romaji or native):
            return None

        cover = row.get("coverImage") or {}
        cover_url = self._clean_text(cover.get("large")) or self._clean_text(cover.get("medium"))
        if not cover_url:
            return None

        season = self._clean_text(row.get("season"))
        season = season.lower() if season else None
        season_year = row.get("seasonYear")
        start_year = (row.get("startDate") or {}).get("year")
        year = season_year if isinstance(season_year, int) else start_year if isinstance(start_year, int) else None

        genres = row.get("genres") if isinstance(row.get("genres"), list) else []
        normalized_genres = [str(item).strip() for item in genres if str(item).strip()]

        return AniListAnime(
            source_id=f"anilist:{row_id}",
            title_english=english,
            title_native=native,
            title_romaji=romaji,
            summary=self._clean_summary(row.get("description")),
            genres=normalized_genres,
            cover_url=cover_url,
            source_cover_url=cover_url,
            year=year,
            season=season,
            status=self._map_status(self._clean_text(row.get("status"))),
            is_adult=bool(row.get("isAdult")),
            popularity=self._popularity_score(row),
        )

    @staticmethod
    def _clean_summary(value: object) -> str | None:
        text = AniListClient._clean_text(value)
        if text is None:
            return None
        no_tags = re.sub(r"<[^>]+>", " ", text)
        no_entities = re.sub(r"&[a-zA-Z#0-9]+;", " ", no_tags)
        compact = re.sub(r"\s+", " ", no_entities).strip()
        return compact or None

    @staticmethod
    def _clean_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _map_status(raw_status: str | None) -> str:
        if raw_status in {"FINISHED", "CANCELLED"}:
            return "finished"
        if raw_status in {"RELEASING", "HIATUS"}:
            return "airing"
        if raw_status == "NOT_YET_RELEASED":
            return "upcoming"
        return "unknown"

    @staticmethod
    def _popularity_score(row: dict) -> int:
        popularity = row.get("popularity")
        favourites = row.get("favourites")
        average_score = row.get("averageScore")
        return (
            (popularity if isinstance(popularity, int) else 0)
            + (favourites if isinstance(favourites, int) else 0) * 4
            + (average_score if isinstance(average_score, int) else 0) * 50
        )
