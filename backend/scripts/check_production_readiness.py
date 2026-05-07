from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import get_settings
from app.core.production import ProductionConfigError, validate_production_settings
from app.db.session import engine


def main() -> int:
    settings = get_settings()
    if not settings.is_production:
        print("APP_ENV must be production for the production readiness check.", file=sys.stderr)
        return 1
    try:
        validate_production_settings(settings)
    except ProductionConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    except Exception as exc:  # noqa: BLE001 - diagnostics should surface the original issue.
        print(f"Database readiness check failed: {exc}", file=sys.stderr)
        return 1

    print("Production readiness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
