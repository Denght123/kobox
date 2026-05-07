from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from hashlib import md5
import logging
import math
from time import monotonic
import re

from sqlalchemy.orm import Session

from app.repositories.anime_repository import AnimeRepository
from app.schemas.anime import AnimeItem, AnimeSuggestionItem
from app.schemas.common import PaginatedResponse
from app.services.anilist_client import AniListAnime, AniListClient
from app.services.anime_mapper import map_anime
from app.services.bangumi_client import BangumiAnime, BangumiClient
from app.services.jikan_client import JikanAnime, JikanClient
from app.services.kitsu_client import KitsuAnime, KitsuClient

logger = logging.getLogger(__name__)
REMOTE_CACHE_TTL_SECONDS = 1800.0
HOT_KEYWORD_BOOSTS: dict[str, tuple[str, ...]] = {
    "你的": ("你的名字", "君の名は", "kiminonawa"),
    "你的名字": ("你的名字", "君の名は", "kiminonawa"),
    "魔女": ("魔女之旅", "魔女の旅々", "majonotabitabi"),
    "四月": ("四月是你的谎言", "四月は君の嘘", "shigatsuwakiminouso"),
    "芙莉莲": ("葬送的芙莉莲", "葬送のフリーレン", "sousounofrieren"),
    "frieren": ("葬送的芙莉莲", "葬送のフリーレン", "sousounofrieren"),
}
HOT_SUGGESTION_TITLES: tuple[tuple[str, str], ...] = (
    ("你的", "你的名字"),
    ("魔女", "魔女之旅"),
    ("四月", "四月是你的谎言"),
    ("芙莉莲", "葬送的芙莉莲"),
)


@dataclass(slots=True)
class RemoteCandidateCacheEntry:
    expires_at: float
    items: list["RemoteAnimeCandidate"]


@dataclass(slots=True)
class RemoteSourceCacheEntry:
    expires_at: float
    item: "RemoteAnimeCandidate"


@dataclass(slots=True)
class RemoteAnimeCandidate:
    source_id: str
    cover_source: str
    cover_url: str
    source_cover_url: str | None
    year: int | None
    season: str | None
    status: str
    genres: list[str]
    summary: str | None
    is_adult: bool
    titles: dict[str, str]
    popularity: int = 0
    rating_rank: int | None = None


class AnimeService:
    _remote_cache: dict[tuple[str, int, bool], RemoteCandidateCacheEntry] = {}
    _source_cache: dict[str, RemoteSourceCacheEntry] = {}

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AnimeRepository(db)
        self.bangumi_client = BangumiClient()
        self.anilist_client = AniListClient()
        self.jikan_client = JikanClient()
        self.kitsu_client = KitsuClient()

    def search(self, *, query: str, page: int, page_size: int, language_code: str) -> PaginatedResponse:
        query_text = query.strip()
        if not query_text:
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)

        remote_limit = max(page * page_size, 12)
        remote_candidates = self._search_remote_candidates(
            query=query_text,
            page=1,
            page_size=remote_limit,
            language_code=language_code,
            fast=True,
        )
        if remote_candidates:
            start = (page - 1) * page_size
            selected_candidates = remote_candidates[start : start + page_size]
            self._remember_candidates(selected_candidates)
            items = self._resolve_search_items(selected_candidates, language_code=language_code)
            if items:
                return PaginatedResponse(
                    items=items,
                    total=len(remote_candidates),
                    page=page,
                    page_size=page_size,
                )

        items, total = self.repo.search(query=query_text, page=page, page_size=page_size)
        return PaginatedResponse(
            items=[map_anime(item, language_code=language_code) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def suggestions(self, *, query: str, page: int, page_size: int, language_code: str) -> PaginatedResponse:
        query_text = query.strip()
        if not query_text:
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)

        seen: set[str] = set()
        items: list[AnimeSuggestionItem] = []

        for keyword, title in HOT_SUGGESTION_TITLES:
            normalized_query = self._normalize_text(query_text)
            normalized_keyword = self._normalize_text(keyword)
            normalized_title = self._normalize_text(title)
            if not normalized_query or (
                not normalized_keyword.startswith(normalized_query)
                and not normalized_title.startswith(normalized_query)
            ):
                continue
            seen.add(normalized_title)
            items.append(AnimeSuggestionItem(id=self._suggestion_id(f"hot:{title}"), title=title))
            if len(items) >= page_size:
                return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)

        local_rows = self.repo.suggestions(query=query_text, limit=page_size * 2, language_code=language_code)
        for anime_id, title in local_rows:
            normalized = self._normalize_text(title)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            items.append(AnimeSuggestionItem(id=anime_id, title=title))
            if len(items) >= page_size:
                return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)

        remote_candidates = self._search_remote_candidates(
            query=query_text,
            page=1,
            page_size=max(page_size * 2, 12),
            language_code=language_code,
            fast=True,
        )

        for candidate in remote_candidates:
            title = self._preferred_candidate_title(candidate, language_code)
            normalized = self._normalize_text(title)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            items.append(AnimeSuggestionItem(id=self._suggestion_id(candidate.source_id), title=title))
            if len(items) >= page_size:
                return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)

        return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)

    def ensure_anime_by_source_id(self, source_id: str):
        existing = self.repo.get_by_source_id(source_id)
        if existing is not None:
            return existing

        cached = self._source_cache.get(source_id)
        now = monotonic()
        if cached and cached.expires_at > now:
            items = self._materialize_candidates([cached.item])
            if items:
                self.db.commit()
                return items[0]

        candidate = self._fetch_candidate_by_source_id(source_id)
        if candidate is not None:
            items = self._materialize_candidates([candidate])
            if items:
                self.db.commit()
                return items[0]

        raise LookupError(source_id)

    def _fetch_candidate_by_source_id(self, source_id: str) -> RemoteAnimeCandidate | None:
        source_name, _, raw_id = source_id.partition(":")
        if not raw_id:
            return None
        try:
            if source_name == "bangumi":
                item = self.bangumi_client.get_subject(int(raw_id))
                return self._candidate_from_bangumi(item) if item else None
            if source_name == "anilist":
                item = self.anilist_client.get_anime(int(raw_id))
                return self._candidate_from_anilist(item) if item else None
            if source_name == "jikan":
                item = self.jikan_client.get_anime(int(raw_id))
                return self._candidate_from_jikan(item) if item else None
            if source_name == "kitsu":
                item = self.kitsu_client.get_anime(raw_id)
                return self._candidate_from_kitsu(item) if item else None
        except Exception as exc:
            logger.warning("Failed to materialize anime %s: %s", source_id, exc)
        return None

    def _resolve_search_items(self, candidates: list[RemoteAnimeCandidate], *, language_code: str) -> list[AnimeItem]:
        return [self._map_candidate_item(candidate, language_code=language_code) for candidate in candidates]

    def _map_candidate_item(self, candidate: RemoteAnimeCandidate, *, language_code: str) -> AnimeItem:
        return AnimeItem(
            id=self._suggestion_id(candidate.source_id),
            source_id=candidate.source_id,
            cover_url=candidate.cover_url,
            source_cover_url=candidate.source_cover_url,
            local_cover_url=None,
            year=candidate.year,
            season=candidate.season,
            status=candidate.status,
            title=self._preferred_candidate_title(candidate, language_code),
            summary=candidate.summary,
            genres=list(candidate.genres),
        )

    def _remember_candidates(self, candidates: list[RemoteAnimeCandidate]) -> None:
        now = monotonic()
        for candidate in candidates:
            self._source_cache[candidate.source_id] = RemoteSourceCacheEntry(
                expires_at=now + REMOTE_CACHE_TTL_SECONDS,
                item=candidate,
            )

    def _materialize_candidates(self, candidates: list[RemoteAnimeCandidate]) -> list:
        payloads = []
        for candidate in candidates:
            translations: dict[str, tuple[str, str | None]] = {}
            for language_code, title in candidate.titles.items():
                cleaned_title = title.strip()
                if not cleaned_title:
                    continue
                translations[language_code] = (cleaned_title, candidate.summary)
            if not translations:
                continue
            payloads.append(
                {
                    "source_id": candidate.source_id,
                    "cover_url": candidate.cover_url,
                    "source_cover_url": candidate.source_cover_url,
                    "year": candidate.year,
                    "season": candidate.season,
                    "status": candidate.status,
                    "genres": candidate.genres,
                    "translations": translations,
                    "cover_source": candidate.cover_source,
                    "is_adult": candidate.is_adult,
                }
            )
        return self.repo.upsert_many(payloads=payloads)

    def _search_remote_candidates(
        self,
        *,
        query: str,
        page: int,
        page_size: int,
        language_code: str,
        fast: bool = False,
    ) -> list[RemoteAnimeCandidate]:
        cache_key = (query.strip().casefold(), page_size, self._contains_cjk(query), fast)
        now = monotonic()
        cached = self._remote_cache.get(cache_key)
        if cached and cached.expires_at > now:
            return list(cached.items)

        if fast and self._contains_cjk(query):
            primary_sources = ["bangumi"]
            secondary_sources: list[str] = ["anilist"]
        elif fast:
            primary_sources = ["anilist", "jikan"]
            secondary_sources = []
        else:
            primary_sources = ["bangumi", "anilist"] if self._contains_cjk(query) else ["anilist", "jikan"]
            secondary_sources = ["jikan", "kitsu"] if self._contains_cjk(query) else ["bangumi", "kitsu"]

        remote_limit = max(page_size, 10)
        results = self._fetch_sources(primary_sources, query=query, page=page, page_size=remote_limit)
        candidates = self._flatten_source_results(results)
        ranked = self._rank_candidates(candidates, query=query, language_code=language_code)

        if secondary_sources and self._should_expand_sources(
            ranked,
            query=query,
            target_size=min(page_size, 8),
            language_code=language_code,
        ):
            extra_results = self._fetch_sources(secondary_sources, query=query, page=page, page_size=remote_limit)
            candidates.extend(self._flatten_source_results(extra_results))
            ranked = self._rank_candidates(candidates, query=query, language_code=language_code)

        self._remote_cache[cache_key] = RemoteCandidateCacheEntry(
            expires_at=now + REMOTE_CACHE_TTL_SECONDS,
            items=list(ranked),
        )
        return ranked

    def _fetch_sources(
        self,
        source_names: list[str],
        *,
        query: str,
        page: int,
        page_size: int,
    ) -> dict[str, list[RemoteAnimeCandidate]]:
        results: dict[str, list[RemoteAnimeCandidate]] = {name: [] for name in source_names}
        fetchers = {
            "bangumi": self._fetch_bangumi,
            "anilist": self._fetch_anilist,
            "jikan": self._fetch_jikan,
            "kitsu": self._fetch_kitsu,
        }
        with ThreadPoolExecutor(max_workers=len(source_names)) as executor:
            future_map = {
                executor.submit(fetchers[name], query=query, page=page, page_size=page_size): name
                for name in source_names
            }
            for future in as_completed(future_map):
                source_name = future_map[future]
                try:
                    results[source_name] = future.result()
                except Exception as exc:
                    logger.warning("Anime source %s failed for query %r: %s", source_name, query, exc)
                    results[source_name] = []
        return results

    def _flatten_source_results(self, source_results: dict[str, list[RemoteAnimeCandidate]]) -> list[RemoteAnimeCandidate]:
        merged: list[RemoteAnimeCandidate] = []
        for items in source_results.values():
            merged.extend(items)
        return merged

    def _fetch_bangumi(self, *, query: str, page: int, page_size: int) -> list[RemoteAnimeCandidate]:
        items = self.bangumi_client.search(query=query, page=page, page_size=page_size)
        return [candidate for candidate in (self._candidate_from_bangumi(item) for item in items) if candidate]

    def _fetch_anilist(self, *, query: str, page: int, page_size: int) -> list[RemoteAnimeCandidate]:
        items = self.anilist_client.search(query=query, page=page, page_size=page_size)
        return [candidate for candidate in (self._candidate_from_anilist(item) for item in items) if candidate]

    def _fetch_jikan(self, *, query: str, page: int, page_size: int) -> list[RemoteAnimeCandidate]:
        items = self.jikan_client.search(query=query, page=page, page_size=page_size)
        return [candidate for candidate in (self._candidate_from_jikan(item) for item in items) if candidate]

    def _fetch_kitsu(self, *, query: str, page: int, page_size: int) -> list[RemoteAnimeCandidate]:
        items = self.kitsu_client.search(query=query, page=page, page_size=page_size)
        return [candidate for candidate in (self._candidate_from_kitsu(item) for item in items) if candidate]

    def _candidate_from_bangumi(self, item: BangumiAnime) -> RemoteAnimeCandidate | None:
        if item.is_adult:
            return None
        return RemoteAnimeCandidate(
            source_id=item.source_id,
            cover_source="bangumi",
            cover_url=item.cover_url,
            source_cover_url=item.source_cover_url,
            year=item.year,
            season=item.season,
            status=item.status,
            genres=[],
            summary=item.summary,
            is_adult=item.is_adult,
            titles={
                "zh-CN": item.title_cn,
                "ja": item.title_native,
            },
            popularity=item.popularity,
            rating_rank=item.rating_rank,
        )

    def _candidate_from_anilist(self, item: AniListAnime) -> RemoteAnimeCandidate | None:
        if item.is_adult:
            return None
        titles = {
            language_code: title
            for language_code, title in {
                "ja": item.title_native,
                "romaji": item.title_romaji,
                "en": item.title_english,
            }.items()
            if title
        }
        if not titles:
            return None
        return RemoteAnimeCandidate(
            source_id=item.source_id,
            cover_source="anilist",
            cover_url=item.cover_url,
            source_cover_url=item.source_cover_url,
            year=item.year,
            season=item.season,
            status=item.status,
            genres=item.genres,
            summary=item.summary,
            is_adult=item.is_adult,
            titles=titles,
            popularity=item.popularity,
        )

    def _candidate_from_jikan(self, item: JikanAnime) -> RemoteAnimeCandidate | None:
        if item.is_adult:
            return None
        titles = {
            language_code: title
            for language_code, title in {
                "en": item.title_english or item.title_default,
                "ja": item.title_japanese,
                "romaji": item.title_default,
            }.items()
            if title
        }
        for index, alias in enumerate(item.title_synonyms[:5], start=1):
            if alias:
                titles[f"alias-{index}"] = alias
        return RemoteAnimeCandidate(
            source_id=item.source_id,
            cover_source="jikan",
            cover_url=item.cover_url,
            source_cover_url=item.source_cover_url,
            year=item.year,
            season=item.season,
            status=item.status,
            genres=item.genres,
            summary=item.summary,
            is_adult=item.is_adult,
            titles=titles,
            popularity=item.popularity,
        )

    def _candidate_from_kitsu(self, item: KitsuAnime) -> RemoteAnimeCandidate | None:
        if item.is_adult:
            return None
        titles = {
            language_code: title
            for language_code, title in {
                "en": item.title_english or item.title_canonical,
                "ja": item.title_japanese,
                "romaji": item.title_romaji or item.title_canonical,
            }.items()
            if title
        }
        for index, alias in enumerate(item.title_synonyms[:5], start=1):
            if alias:
                titles[f"alias-{index}"] = alias
        return RemoteAnimeCandidate(
            source_id=item.source_id,
            cover_source="kitsu",
            cover_url=item.cover_url,
            source_cover_url=item.source_cover_url,
            year=item.year,
            season=item.season,
            status=item.status,
            genres=[],
            summary=item.summary,
            is_adult=item.is_adult,
            titles=titles,
            popularity=item.popularity,
        )

    def _rank_candidates(
        self,
        items: list[RemoteAnimeCandidate],
        *,
        query: str,
        language_code: str,
    ) -> list[RemoteAnimeCandidate]:
        deduped: list[RemoteAnimeCandidate] = []

        for item in items:
            matched_index = None
            current_aliases = self._alias_set(item)
            for index, existing in enumerate(deduped):
                if self._should_merge(existing, item, current_aliases):
                    matched_index = index
                    break
            if matched_index is None:
                deduped.append(item)
                continue
            if self._source_weight(item) < self._source_weight(deduped[matched_index]):
                deduped[matched_index] = item

        contains_cjk = self._contains_cjk(query)
        normalized_query = self._normalize_text(query)

        def score(candidate: RemoteAnimeCandidate) -> tuple[int, int, int, int, int, float, int, int]:
            best = min(
                (self._score_title(title, normalized_query) for title in self._alias_set(candidate)),
                default=(99, 99),
            )
            has_preferred_localized_title = 0
            if contains_cjk and candidate.titles.get(language_code):
                has_preferred_localized_title = -1
            elif contains_cjk and candidate.titles.get("zh-CN"):
                has_preferred_localized_title = -1
            rank_score = candidate.rating_rank if candidate.rating_rank is not None else 999999
            return (
                self._keyword_boost(candidate, query),
                best[0],
                has_preferred_localized_title,
                rank_score,
                -self._popularity_bucket(candidate.popularity),
                -math.log10(max(candidate.popularity, 1)),
                best[1],
                self._source_weight(candidate),
            )

        return sorted(deduped, key=score)

    def _should_merge(
        self,
        left: RemoteAnimeCandidate,
        right: RemoteAnimeCandidate,
        right_aliases: set[str],
    ) -> bool:
        left_aliases = self._alias_set(left)
        if not left_aliases or not right_aliases:
            return False
        same_year = left.year is None or right.year is None or abs(left.year - right.year) <= 1
        return same_year and bool(left_aliases & right_aliases)

    def _should_expand_sources(
        self,
        items: list[RemoteAnimeCandidate],
        *,
        query: str,
        target_size: int,
        language_code: str,
    ) -> bool:
        if len(items) < max(3, target_size):
            return True
        top_titles = [self._preferred_candidate_title(item, language_code) for item in items[:3]]
        normalized_query = self._normalize_text(query)
        best = min((self._score_title(self._normalize_text(title), normalized_query) for title in top_titles), default=(99, 99))
        return best[0] > 1

    def _preferred_candidate_title(self, candidate: RemoteAnimeCandidate, language_code: str) -> str:
        for key in (language_code, "zh-CN", "ja", "en", "romaji"):
            title = candidate.titles.get(key)
            if title:
                return title
        for title in candidate.titles.values():
            if title:
                return title
        return candidate.source_id

    def _alias_set(self, candidate: RemoteAnimeCandidate) -> set[str]:
        return {
            self._normalize_text(title)
            for title in candidate.titles.values()
            if title and self._normalize_text(title)
        }

    @staticmethod
    def _source_weight(candidate: RemoteAnimeCandidate) -> int:
        if candidate.cover_source == "bangumi":
            return 0
        if candidate.cover_source == "jikan":
            return 1
        if candidate.cover_source == "kitsu":
            return 2
        if candidate.cover_source == "anilist":
            return 3
        return 9

    @staticmethod
    def _score_title(title: str, normalized_query: str) -> tuple[int, int]:
        if not normalized_query:
            return (99, 99)
        if title == normalized_query:
            return (0, 0)
        if title.startswith(normalized_query):
            return (1, max(len(title) - len(normalized_query), 0))
        if normalized_query in title:
            return (2, max(len(title) - len(normalized_query), 0))
        return (9, len(title))

    def _keyword_boost(self, candidate: RemoteAnimeCandidate, query: str) -> int:
        normalized_query = self._normalize_text(query)
        for keyword, boosted_aliases in HOT_KEYWORD_BOOSTS.items():
            if not normalized_query or not self._normalize_text(keyword).startswith(normalized_query):
                continue
            aliases = self._alias_set(candidate)
            if any(self._normalize_text(boosted_alias) in aliases for boosted_alias in boosted_aliases):
                return -2
        return 0

    @staticmethod
    def _popularity_bucket(popularity: int) -> int:
        if popularity >= 1000000:
            return 6
        if popularity >= 300000:
            return 5
        if popularity >= 100000:
            return 4
        if popularity >= 30000:
            return 3
        if popularity >= 10000:
            return 2
        if popularity >= 1000:
            return 1
        return 0

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"[\s\W_]+", "", value.casefold())

    @staticmethod
    def _contains_cjk(value: str) -> bool:
        return bool(re.search(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", value))

    @staticmethod
    def _suggestion_id(source_id: str) -> int:
        digest = md5(source_id.encode("utf-8"), usedforsecurity=False).hexdigest()
        return -int(digest[:8], 16)
