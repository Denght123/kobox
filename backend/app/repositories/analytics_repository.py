from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analytics_event import AnalyticsEvent


class AnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record_event(
        self,
        *,
        event_name: str,
        user_id: int | None = None,
        metadata: dict | None = None,
    ) -> AnalyticsEvent:
        event = AnalyticsEvent(
            user_id=user_id,
            event_name=event_name,
            metadata_json=metadata or {},
        )
        self.db.add(event)
        self.db.flush()
        return event

    def count_events_since(self, *, event_name: str, since: datetime) -> int:
        stmt = select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.event_name == event_name,
            AnalyticsEvent.created_at >= since,
        )
        return int(self.db.scalar(stmt) or 0)
