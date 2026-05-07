from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.core.production import validate_production_settings
from app.db.base import Base
from app.db.init_db import seed_data
from app.db.model_registry import *  # noqa: F401,F403
from app.db.session import SessionLocal, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("postgresql"):
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    if settings.seed_on_startup:
        with SessionLocal() as db:
            seed_data(db)
    yield


settings = get_settings()
validate_production_settings(settings)
settings.uploads_path.mkdir(parents=True, exist_ok=True)
app = FastAPI(title=settings.app_name, debug=settings.app_debug, lifespan=lifespan)
if settings.trusted_hosts_list:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts_list)
if settings.enable_security_headers:
    app.add_middleware(SecurityHeadersMiddleware, settings=settings)
if settings.enable_rate_limit:
    app.add_middleware(RateLimitMiddleware, settings=settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers_list,
)
app.mount(settings.uploads_url_prefix, StaticFiles(directory=str(settings.uploads_path)), name="uploads")

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("select 1"))
    return {"status": "ready"}


app.include_router(api_router, prefix="/api")
