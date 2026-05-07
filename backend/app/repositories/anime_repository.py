import json

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.anime import Anime, AnimeTranslation


class AnimeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, anime_id: int) -> Anime | None:
        stmt = select(Anime).options(joinedload(Anime.translations)).where(Anime.id == anime_id)
        return self.db.scalars(stmt).first()

    def get_by_source_id(self, source_id: str) -> Anime | None:
        stmt = select(Anime).options(joinedload(Anime.translations)).where(Anime.source_id == source_id)
        return self.db.scalars(stmt).first()

    def get_by_source_ids(self, source_ids: list[str]) -> dict[str, Anime]:
        normalized_ids = [source_id for source_id in source_ids if source_id]
        if not normalized_ids:
            return {}
        stmt = (
            select(Anime)
            .options(joinedload(Anime.translations))
            .where(Anime.source_id.in_(normalized_ids))
        )
        rows = list(self.db.scalars(stmt).unique())
        return {row.source_id: row for row in rows if row.source_id}

    def search(self, *, query: str, page: int, page_size: int) -> tuple[list[Anime], int]:
        search_like = f"%{query.strip()}%"
        base_stmt = (
            select(Anime.id)
            .join(AnimeTranslation, AnimeTranslation.anime_id == Anime.id)
            .where(Anime.is_adult.is_(False))
            .where(AnimeTranslation.title.ilike(search_like))
            .distinct()
        )

        total = self.db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

        ids_stmt = base_stmt.offset((page - 1) * page_size).limit(page_size)
        anime_ids = list(self.db.scalars(ids_stmt))
        if not anime_ids:
            return [], total

        stmt = (
            select(Anime)
            .options(joinedload(Anime.translations))
            .where(Anime.id.in_(anime_ids))
            .order_by(Anime.id.desc())
        )
        items = list(self.db.scalars(stmt).unique())
        return items, total

    def suggestions(
        self,
        *,
        query: str,
        limit: int = 10,
        language_code: str = "zh-CN",
    ) -> list[tuple[int, str]]:
        search_like = f"%{query.strip()}%"
        language_rank = case(
            (AnimeTranslation.language_code == language_code, 0),
            (AnimeTranslation.language_code == "zh-CN", 1),
            (AnimeTranslation.language_code == "ja", 2),
            (AnimeTranslation.language_code == "en", 3),
            else_=4,
        )
        stmt = (
            select(Anime.id, AnimeTranslation.title)
            .join(AnimeTranslation, AnimeTranslation.anime_id == Anime.id)
            .where(Anime.is_adult.is_(False))
            .where(AnimeTranslation.title.ilike(search_like))
            .order_by(Anime.id.desc(), language_rank)
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()
        seen: set[int] = set()
        suggestions: list[tuple[int, str]] = []
        for anime_id, title in rows:
            if anime_id in seen:
                continue
            seen.add(anime_id)
            suggestions.append((anime_id, title))
        return suggestions

    def upsert_many(
        self,
        *,
        payloads: list[dict[str, object]],
    ) -> list[Anime]:
        if not payloads:
            return []

        deduped_payloads: list[dict[str, object]] = []
        ordered_source_ids: list[str] = []
        seen: set[str] = set()
        for payload in payloads:
            source_id = str(payload.get("source_id", "")).strip()
            if not source_id or source_id in seen:
                continue
            seen.add(source_id)
            ordered_source_ids.append(source_id)
            deduped_payloads.append(payload)

        existing_by_source = self.get_by_source_ids(ordered_source_ids)
        items: list[Anime] = []

        for payload in deduped_payloads:
            source_id = str(payload["source_id"])
            translations = payload.get("translations")
            if not isinstance(translations, dict):
                continue

            anime = existing_by_source.get(source_id)
            if anime is None:
                anime = Anime(
                    source_id=source_id,
                    cover_url=str(payload["cover_url"]),
                    source_cover_url=payload.get("source_cover_url"),
                    local_cover_url=None,
                    cover_source=str(payload.get("cover_source", "seed")),
                    is_adult=bool(payload.get("is_adult", False)),
                    year=payload.get("year"),
                    season=payload.get("season"),
                    status=str(payload.get("status", "unknown")),
                    genres_json=json.dumps(payload.get("genres", []), ensure_ascii=False),
                )
                self.db.add(anime)
                existing_by_source[source_id] = anime
            else:
                anime.cover_url = str(payload["cover_url"])
                anime.source_cover_url = payload.get("source_cover_url")
                anime.cover_source = str(payload.get("cover_source", anime.cover_source))
                anime.is_adult = bool(payload.get("is_adult", anime.is_adult))
                anime.year = payload.get("year")
                anime.season = payload.get("season")
                anime.status = str(payload.get("status", anime.status))
                anime.genres_json = json.dumps(payload.get("genres", []), ensure_ascii=False)

            existing_by_lang = {row.language_code: row for row in anime.translations}
            for lang, value in translations.items():
                if not isinstance(lang, str):
                    continue
                if not isinstance(value, tuple) or len(value) != 2:
                    continue
                title, summary = value
                if not title:
                    continue
                current = existing_by_lang.get(lang)
                if current is None:
                    anime.translations.append(
                        AnimeTranslation(
                            language_code=lang,
                            title=str(title),
                            summary=str(summary) if summary else None,
                        )
                    )
                else:
                    current.title = str(title)
                    current.summary = str(summary) if summary else None

            items.append(anime)

        if items:
            self.db.flush()
        return items

    def upsert_anilist(
        self,
        *,
        source_id: str,
        cover_url: str,
        source_cover_url: str | None,
        year: int | None,
        season: str | None,
        status: str,
        genres: list[str],
        translations: dict[str, tuple[str, str | None]],
        cover_source: str = "anilist",
        is_adult: bool = False,
    ) -> Anime:
        items = self.upsert_many(
            payloads=[
                {
                    "source_id": source_id,
                    "cover_url": cover_url,
                    "source_cover_url": source_cover_url,
                    "year": year,
                    "season": season,
                    "status": status,
                    "genres": genres,
                    "translations": translations,
                    "cover_source": cover_source,
                    "is_adult": is_adult,
                }
            ]
        )
        return items[0]
