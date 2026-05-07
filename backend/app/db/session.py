from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

connect_args: dict[str, object] = {}
engine_kwargs: dict[str, object] = {
    "future": True,
    "connect_args": connect_args,
}

if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif settings.database_url.startswith("postgresql"):
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 2
    engine_kwargs["max_overflow"] = 3
    engine_kwargs["pool_timeout"] = 10
    engine_kwargs["pool_use_lifo"] = True
    engine_kwargs["pool_recycle"] = 1800
    if settings.uses_supabase_transaction_pooler:
        if settings.database_url.startswith("postgresql+psycopg://"):
            connect_args["prepare_threshold"] = None

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
