from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from time import monotonic
import re

import httpx

from app.core.config import get_settings

SEARCH_CACHE_TTL_SECONDS = 600.0


@dataclass(slots=True)
class BangumiCacheEntry:
    expires_at: float
    items: list["BangumiAnime"]


@dataclass(slots=True)
class BangumiAnime:
    source_id: str
    title_cn: str
    title_native: str
    summary: str | None
    cover_url: str
    source_cover_url: str | None
    year: int | None
    season: str | None
    status: str
    is_adult: bool
    popularity: int
    rating_rank: int | None


class BangumiClient:
    _search_cache: dict[tuple[str, int, int], BangumiCacheEntry] = {}
    _subject_cache: dict[int, BangumiAnime | None] = {}

    def __init__(self) -> None:
        self.settings = get_settings()
        self._base_url = self.settings.bangumi_api_url.rstrip("/")
        self._user_agent = self.settings.bangumi_user_agent

    def search(self, *, query: str, page: int, page_size: int) -> list[BangumiAnime]:
        cache_key = (query.strip().casefold(), page, page_size)
        cached = self._search_cache.get(cache_key)
        now = monotonic()
        if cached and cached.expires_at > now:
            return list(cached.items)

        payload = {
            "keyword": query,
            "filter": {"type": [2]},
        }
        if page > 1:
            payload["offset"] = (page - 1) * page_size
        if page_size > 0:
            payload["limit"] = page_size

        body = self._request("POST", "/search/subjects", json=payload)
        rows = body.get("data", [])
        if not isinstance(rows, list):
            return []

        result: list[BangumiAnime] = []
        for row in rows:
            anime = self._map_row(row)
            if anime is not None:
                result.append(anime)
        self._search_cache[cache_key] = BangumiCacheEntry(
            expires_at=now + SEARCH_CACHE_TTL_SECONDS,
            items=list(result),
        )
        return result

    def get_subject(self, subject_id: int) -> BangumiAnime | None:
        if subject_id in self._subject_cache:
            return self._subject_cache[subject_id]
        body = self._request("GET", f"/subjects/{subject_id}")
        anime = self._map_row(body)
        self._subject_cache[subject_id] = anime
        return anime

    def _map_row(self, row: dict) -> BangumiAnime | None:
        if not isinstance(row, dict):
            return None
        row_id = row.get("id")
        if not row_id:
            return None

        title_cn = self._clean_text(row.get("name_cn")) or self._clean_text(row.get("name"))
        title_native = self._clean_text(row.get("name")) or title_cn
        if not title_cn or not title_native:
            return None

        cover = row.get("images") or {}
        cover_url = (
            self._clean_text(cover.get("large"))
            or self._clean_text(cover.get("medium"))
            or self._clean_text(row.get("image"))
        )
        if not cover_url:
            return None

        date_value = self._clean_text(row.get("date"))
        year, season = self._parse_date(date_value)
        summary = self._clean_summary(row.get("summary"))
        rating = row.get("rating") if isinstance(row.get("rating"), dict) else {}
        rating_total = rating.get("total")
        rating_rank = rating.get("rank")
        normalized_rank = rating_rank if isinstance(rating_rank, int) and rating_rank > 0 else None

        return BangumiAnime(
            source_id=f"bangumi:{row_id}",
            title_cn=title_cn,
            title_native=title_native,
            summary=summary,
            cover_url=cover_url,
            source_cover_url=cover_url,
            year=year,
            season=season,
            status="unknown",
            is_adult=bool(row.get("nsfw")),
            popularity=rating_total if isinstance(rating_total, int) else 0,
            rating_rank=normalized_rank,
        )

    @staticmethod
    def _clean_summary(value: object) -> str | None:
        text = BangumiClient._clean_text(value)
        if text is None:
            return None
        no_tags = re.sub(r"<[^>]+>", " ", text)
        compact = re.sub(r"\s+", " ", no_tags).strip()
        return compact or None

    @staticmethod
    def _clean_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _parse_date(date_value: str | None) -> tuple[int | None, str | None]:
        if not date_value:
            return None, None
        try:
            parsed = datetime.fromisoformat(date_value)
        except ValueError:
            return None, None
        month = parsed.month
        if month in {3, 4, 5}:
            season = "spring"
        elif month in {6, 7, 8}:
            season = "summer"
        elif month in {9, 10, 11}:
            season = "fall"
        else:
            season = "winter"
        return parsed.year, season

    def _request(self, method: str, path: str, **kwargs: object) -> dict:
        with httpx.Client(
            timeout=self.settings.bangumi_timeout_seconds,
            headers={"User-Agent": self._user_agent},
            trust_env=False,
        ) as client:
            response = client.request(method, f"{self._base_url}{path}", **kwargs)
            response.raise_for_status()
            body = response.json()
        if not isinstance(body, dict):
            return {}
        return body
