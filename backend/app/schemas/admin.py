from pydantic import BaseModel


class DailyRegistrationCount(BaseModel):
    day: str
    registrations: int


class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    today_users: int
    last_7_days_users: int
    last_30_days_users: int
    total_collections: int
    users_with_collection: int
    total_favorites: int
    users_with_favorites: int
    registration_events_today: int
    registration_events_last_7_days: int
    daily_registrations: list[DailyRegistrationCount]
