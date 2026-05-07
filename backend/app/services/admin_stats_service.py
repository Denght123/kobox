from datetime import datetime, timedelta, timezone

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_collection import UserCollection
from app.models.user_favorite_rank import UserFavoriteRank
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.admin import AdminStatsResponse, DailyRegistrationCount


class AdminStatsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.analytics_repo = AnalyticsRepository(db)

    def get_stats(self) -> AdminStatsResponse:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seven_days_start = today_start - timedelta(days=6)
        thirty_days_start = today_start - timedelta(days=29)

        return AdminStatsResponse(
            total_users=self._count_users(),
            active_users=self._count_users(active_only=True),
            today_users=self._count_users_since(today_start),
            last_7_days_users=self._count_users_since(seven_days_start),
            last_30_days_users=self._count_users_since(thirty_days_start),
            total_collections=self._count_rows(UserCollection.id),
            users_with_collection=self._count_distinct(UserCollection.user_id),
            total_favorites=self._count_rows(UserFavoriteRank.id),
            users_with_favorites=self._count_distinct(UserFavoriteRank.user_id),
            registration_events_today=self.analytics_repo.count_events_since(
                event_name="user_registered",
                since=today_start,
            ),
            registration_events_last_7_days=self.analytics_repo.count_events_since(
                event_name="user_registered",
                since=seven_days_start,
            ),
            daily_registrations=self._daily_registrations(days=30),
        )

    def _count_users(self, *, active_only: bool = False) -> int:
        stmt = select(func.count(User.id))
        if active_only:
            stmt = stmt.where(User.is_active.is_(True))
        return int(self.db.scalar(stmt) or 0)

    def _count_users_since(self, since: datetime) -> int:
        stmt = select(func.count(User.id)).where(User.created_at >= since)
        return int(self.db.scalar(stmt) or 0)

    def _count_rows(self, column) -> int:
        return int(self.db.scalar(select(func.count(column))) or 0)

    def _count_distinct(self, column) -> int:
        return int(self.db.scalar(select(func.count(distinct(column)))) or 0)

    def _daily_registrations(self, *, days: int) -> list[DailyRegistrationCount]:
        now = datetime.now(timezone.utc)
        start_day = (now - timedelta(days=days - 1)).date()
        day_expr = func.date(User.created_at)
        stmt = (
            select(day_expr.label("day"), func.count(User.id).label("registrations"))
            .where(User.created_at >= datetime.combine(start_day, datetime.min.time(), tzinfo=timezone.utc))
            .group_by(day_expr)
            .order_by(day_expr)
        )
        rows = self.db.execute(stmt).all()
        counts_by_day = {str(row.day): int(row.registrations) for row in rows}
        return [
            DailyRegistrationCount(
                day=str(start_day + timedelta(days=offset)),
                registrations=counts_by_day.get(str(start_day + timedelta(days=offset)), 0),
            )
            for offset in range(days)
        ]
