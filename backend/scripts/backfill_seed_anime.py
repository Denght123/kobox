from __future__ import annotations

import json
from pathlib import Path
import sys

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.anime_seed_data import SEED_ANIME_ITEMS
from app.db.session import SessionLocal
from app.models.anime import Anime, AnimeTranslation


def _upsert_seed_anime(db) -> None:
    for item in SEED_ANIME_ITEMS:
        anime = db.scalar(select(Anime).where(Anime.source_id == item["source_id"]))
        if anime is None:
            anime = Anime(
                source_id=item["source_id"],
                cover_url=item["cover_url"],
                source_cover_url=item["cover_url"],
                local_cover_url=None,
                cover_source="bangumi",
                is_adult=False,
                year=item["year"],
                season=item["season"],
                status=item["status"],
                genres_json=json.dumps(item.get("genres", []), ensure_ascii=False),
            )
            db.add(anime)
            db.flush()
        else:
            anime.cover_url = item["cover_url"]
            anime.source_cover_url = item["cover_url"]
            anime.cover_source = "bangumi"
            anime.is_adult = False
            anime.year = item["year"]
            anime.season = item["season"]
            anime.status = item["status"]
            anime.genres_json = json.dumps(item.get("genres", []), ensure_ascii=False)
            db.add(anime)
            db.flush()

        existing_by_lang = {row.language_code: row for row in anime.translations}
        for language_code, title, summary in item["translations"]:
            current = existing_by_lang.get(language_code)
            if current is None:
                anime.translations.append(
                    AnimeTranslation(
                        language_code=language_code,
                        title=title,
                        summary=summary,
                    )
                )
            else:
                current.title = title
                current.summary = summary
                db.add(current)

        db.add(anime)

    db.commit()


def main() -> None:
    with SessionLocal() as db:
        _upsert_seed_anime(db)


if __name__ == "__main__":
    main()
