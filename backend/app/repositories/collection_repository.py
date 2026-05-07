from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.anime import Anime
from app.models.user_collection import CollectionStatus, UserCollection


class CollectionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id_for_user(self, *, user_id: int, collection_id: int) -> UserCollection | None:
        stmt = (
            select(UserCollection)
            .options(joinedload(UserCollection.anime).joinedload(Anime.translations))
            .where(UserCollection.user_id == user_id, UserCollection.id == collection_id)
        )
        return self.db.scalars(stmt).first()

    def get_by_user_anime(self, *, user_id: int, anime_id: int) -> UserCollection | None:
        stmt = select(UserCollection).where(UserCollection.user_id == user_id, UserCollection.anime_id == anime_id)
        return self.db.scalars(stmt).first()

    def create(self, *, user_id: int, anime_id: int, status: CollectionStatus) -> UserCollection:
        item = UserCollection(user_id=user_id, anime_id=anime_id, collection_status=status)
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)
        return item

    def list_by_user(
        self,
        *,
        user_id: int,
        page: int,
        page_size: int,
        status: CollectionStatus | None = None,
        include_total: bool = True,
    ) -> tuple[list[UserCollection], int]:
        filters = [UserCollection.user_id == user_id]
        if status is not None:
            filters.append(UserCollection.collection_status == status)

        total = 0
        if include_total:
            base_stmt = select(UserCollection.id).where(*filters)
            total = self.db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

        stmt = (
            select(UserCollection)
            .options(joinedload(UserCollection.anime).joinedload(Anime.translations))
            .where(*filters)
            .order_by(UserCollection.added_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt).unique())
        return items, total if include_total else len(items)

    def delete(self, item: UserCollection) -> None:
        self.db.delete(item)
        self.db.flush()
