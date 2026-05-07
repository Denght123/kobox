from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.db.session import get_db
from app.schemas.admin import AdminStatsResponse
from app.services.admin_stats_service import AdminStatsService

router = APIRouter()


def verify_admin_stats_token(
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None),
) -> None:
    settings = get_settings()
    expected_token = settings.admin_stats_token
    if not expected_token:
        raise AppException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="admin_stats_not_configured",
            message="Admin stats token is not configured",
        )

    bearer_token = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer_token = authorization[7:].strip()

    provided_token = x_admin_token or bearer_token
    if provided_token != expected_token:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="invalid_admin_token",
            message="Invalid admin stats token",
        )


@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    _: None = Depends(verify_admin_stats_token),
    db: Session = Depends(get_db),
) -> AdminStatsResponse:
    return AdminStatsService(db).get_stats()
