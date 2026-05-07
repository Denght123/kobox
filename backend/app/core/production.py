from app.core.config import Settings


LOCAL_ORIGIN_MARKERS = ("localhost", "127.0.0.1", "0.0.0.0")
INSECURE_SECRET_KEYS = {"replace_me", "replace_this_with_a_long_random_secret", "change_me"}


class ProductionConfigError(RuntimeError):
    pass


def validate_production_settings(settings: Settings) -> None:
    if not settings.is_production:
        return

    problems: list[str] = []
    if settings.app_debug:
        problems.append("APP_DEBUG must be false in production")
    if settings.secret_key in INSECURE_SECRET_KEYS or len(settings.secret_key) < 32:
        problems.append("SECRET_KEY must be a strong random value with at least 32 characters")
    if not settings.admin_stats_token or len(settings.admin_stats_token) < 24:
        problems.append("ADMIN_STATS_TOKEN must be configured with a strong random value")
    if settings.database_url.startswith("sqlite"):
        problems.append("DATABASE_URL must point to PostgreSQL/Supabase in production")
    if settings.auto_create_tables:
        problems.append("AUTO_CREATE_TABLES must be false in production; use Alembic migrations")
    if settings.seed_on_startup:
        problems.append("SEED_ON_STARTUP must be false in production")
    if "*" in settings.cors_allow_origins_list:
        problems.append("CORS_ALLOW_ORIGINS must not contain '*' in production")
    if any(_contains_local_marker(origin) for origin in settings.cors_allow_origins_list):
        problems.append("CORS_ALLOW_ORIGINS must use your production frontend domain")
    if any(_contains_local_marker(host) for host in settings.trusted_hosts_list):
        problems.append("TRUSTED_HOSTS must use your production API host/domain")
    if _contains_local_marker(settings.password_reset_url):
        problems.append("PASSWORD_RESET_URL must use your production frontend domain")
    if _contains_local_marker(settings.public_site_url):
        problems.append("PUBLIC_SITE_URL must use your production frontend domain")
    if not all((settings.smtp_host, settings.smtp_from_email)):
        problems.append("SMTP_HOST and SMTP_FROM_EMAIL are required for password reset emails")

    if problems:
        joined = "\n- ".join(problems)
        raise ProductionConfigError(f"Production configuration is incomplete:\n- {joined}")


def _contains_local_marker(value: str) -> bool:
    normalized = value.lower()
    return any(marker in normalized for marker in LOCAL_ORIGIN_MARKERS)
