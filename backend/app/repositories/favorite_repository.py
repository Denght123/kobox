from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.models.anime import Anime
from app.models.user_favorite_rank import UserFavoriteRank


class FavoriteRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_user(self, *, user_id: int) -> list[UserFavoriteRank]:
        stmt = (
            select(UserFavoriteRank)
            .options(joinedload(UserFavoriteRank.anime).joinedload(Anime.translations))
            .where(UserFavoriteRank.user_id == user_id)
            .order_by(UserFavoriteRank.rank_order.asc())
        )
        return list(self.db.scalars(stmt).unique())

    def replace_all(self, *, user_id: int, ranks: list[tuple[int, int]]) -> list[UserFavoriteRank]:
        self.db.execute(delete(UserFavoriteRank).where(UserFavoriteRank.user_id == user_id))
        for anime_id, rank_order in ranks:
            self.db.add(UserFavoriteRank(user_id=user_id, anime_id=anime_id, rank_order=rank_order))
        self.db.flush()
        return self.list_by_user(user_id=user_id)

    def delete_by_user_anime(self, *, user_id: int, anime_id: int) -> None:
        self.db.execute(
            delete(UserFavoriteRank).where(
                UserFavoriteRank.user_id == user_id,
                UserFavoriteRank.anime_id == anime_id,
            ),
        )
        self.db.flush()
