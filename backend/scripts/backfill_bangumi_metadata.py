from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import joinedload

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.session import SessionLocal
from app.models.anime import Anime, AnimeTranslation
from app.services.bangumi_client import BangumiClient

SEED_SOURCE_MAPPING = {
    "seed-frieren": 400602,
    "seed-edgerunners": 309311,
    "seed-violet": 183878,
    "seed-bocchi": 328609,
    "seed-apothecary": 420628,
    "seed-jjk": 294993,
}


def main() -> None:
    client = BangumiClient()
    updated = 0

    with SessionLocal() as db:
        anime_rows = list(
            db.scalars(
                select(Anime)
                .options(joinedload(Anime.translations))
                .order_by(Anime.id.asc())
            ).unique()
        )

        for anime in anime_rows:
            subject_id = SEED_SOURCE_MAPPING.get(anime.source_id or "")
            if subject_id is None:
                continue

            subject = client.get_subject(subject_id)
            if subject is None or subject.is_adult:
                continue

            anime.source_id = subject.source_id
            anime.cover_url = subject.cover_url
            anime.source_cover_url = subject.source_cover_url
            anime.cover_source = "bangumi"
            anime.is_adult = False
            anime.year = subject.year
            anime.season = subject.season
            anime.status = subject.status

            translations = {
                "zh-CN": (subject.title_cn, subject.summary),
                "ja": (subject.title_native, subject.summary),
            }
            current_by_lang = {row.language_code: row for row in anime.translations}
            for language_code, (title, summary) in translations.items():
                row = current_by_lang.get(language_code)
                if row is None:
                    anime.translations.append(
                        AnimeTranslation(language_code=language_code, title=title, summary=summary)
                    )
                else:
                    row.title = title
                    row.summary = summary
            updated += 1

        delete_result = db.execute(
            delete(Anime)
            .where(
                or_(
                    Anime.cover_source == "anilist",
                    Anime.source_id.like("anilist:%"),
                )
            )
            .where(~Anime.collections.any())
            .where(~Anime.favorite_ranks.any())
        )
        db.commit()

    deleted = delete_result.rowcount or 0
    print(f"Updated {updated} anime rows.")
    print(f"Deleted {deleted} orphan AniList rows.")


if __name__ == "__main__":
    main()
