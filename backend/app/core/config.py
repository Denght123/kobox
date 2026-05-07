from functools import lru_cache
import json
from pathlib import Path

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Kobox API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")

    database_url: str = Field(default="sqlite:///./kobox.db", alias="DATABASE_URL")
    secret_key: str = Field(default="replace_me", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=14, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    seed_on_startup: bool = Field(default=True, alias="SEED_ON_STARTUP")
    auto_create_tables: bool = Field(default=True, alias="AUTO_CREATE_TABLES")
    cors_allow_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ALLOW_ORIGINS",
    )
    cors_allow_methods: str = Field(
        default="GET,POST,PUT,PATCH,DELETE,OPTIONS",
        alias="CORS_ALLOW_METHODS",
    )
    cors_allow_headers: str = Field(default="*", alias="CORS_ALLOW_HEADERS")
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    trusted_hosts: str = Field(default="localhost,127.0.0.1,testserver", alias="TRUSTED_HOSTS")
    enable_security_headers: bool = Field(default=True, alias="ENABLE_SECURITY_HEADERS")
    enable_rate_limit: bool = Field(default=True, alias="ENABLE_RATE_LIMIT")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")
    rate_limit_api_requests: int = Field(default=240, alias="RATE_LIMIT_API_REQUESTS")
    rate_limit_auth_requests: int = Field(default=20, alias="RATE_LIMIT_AUTH_REQUESTS")
    rate_limit_search_requests: int = Field(default=90, alias="RATE_LIMIT_SEARCH_REQUESTS")
    admin_stats_token: str = Field(default="", alias="ADMIN_STATS_TOKEN")

    uploads_dir: str = Field(default="uploads", alias="UPLOADS_DIR")
    uploads_url_prefix: str = Field(default="/uploads", alias="UPLOADS_URL_PREFIX")
    upload_max_bytes: int = Field(default=5 * 1024 * 1024, alias="UPLOAD_MAX_BYTES")
    upload_allowed_image_types: str = Field(
        default="image/jpeg,image/png,image/webp,image/gif",
        alias="UPLOAD_ALLOWED_IMAGE_TYPES",
    )
    password_reset_token_expire_minutes: int = Field(default=30, alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES")
    password_reset_url: str = Field(default="http://127.0.0.1:5173/auth", alias="PASSWORD_RESET_URL")
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="", alias="SMTP_FROM_EMAIL")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, alias="SMTP_USE_SSL")
    public_site_url: str = Field(default="http://127.0.0.1:5173", alias="PUBLIC_SITE_URL")

    anilist_api_url: str = Field(default="https://graphql.anilist.co", alias="ANILIST_API_URL")
    anilist_timeout_seconds: float = Field(default=5.0, alias="ANILIST_TIMEOUT_SECONDS")
    bangumi_api_url: str = Field(default="https://api.bgm.tv/v0", alias="BANGUMI_API_URL")
    bangumi_timeout_seconds: float = Field(default=5.0, alias="BANGUMI_TIMEOUT_SECONDS")
    bangumi_user_agent: str = Field(
        default="kobox/1.0 (https://github.com/openai/codex)",
        alias="BANGUMI_USER_AGENT",
    )
    jikan_api_url: str = Field(default="https://api.jikan.moe/v4", alias="JIKAN_API_URL")
    jikan_timeout_seconds: float = Field(default=5.0, alias="JIKAN_TIMEOUT_SECONDS")
    kitsu_api_url: str = Field(default="https://kitsu.app/api/edge", alias="KITSU_API_URL")
    kitsu_timeout_seconds: float = Field(default=5.0, alias="KITSU_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        url = str(value).strip()
        if not url:
            return "sqlite:///./kobox.db"
        if url.startswith("postgres://"):
            return f"postgresql+psycopg://{url[len('postgres://'):]}"
        if url.startswith("postgresql://"):
            return f"postgresql+psycopg://{url[len('postgresql://'):]}"
        return url

    @field_validator("uploads_url_prefix", mode="after")
    @classmethod
    def _normalize_uploads_prefix(cls, value: str) -> str:
        prefix = value.strip()
        if not prefix:
            return "/uploads"
        if not prefix.startswith("/"):
            prefix = f"/{prefix}"
        return prefix.rstrip("/") or "/uploads"

    @property
    def uses_supabase_transaction_pooler(self) -> bool:
        return ".pooler.supabase.com:6543/" in self.database_url

    @property
    def uploads_path(self) -> Path:
        return Path(self.uploads_dir)

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return self._parse_list(self.cors_allow_origins)

    @property
    def cors_allow_methods_list(self) -> list[str]:
        return self._parse_list(self.cors_allow_methods)

    @property
    def cors_allow_headers_list(self) -> list[str]:
        return self._parse_list(self.cors_allow_headers)

    @property
    def trusted_hosts_list(self) -> list[str]:
        return self._parse_list(self.trusted_hosts)

    @property
    def upload_allowed_image_types_list(self) -> list[str]:
        return self._parse_list(self.upload_allowed_image_types)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @staticmethod
    def _parse_list(value: str) -> list[str]:
        raw = value.strip()
        if not raw:
            return []
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
