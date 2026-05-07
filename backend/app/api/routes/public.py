from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_language_code
from app.db.session import get_db
from app.models.user_collection import CollectionStatus
from app.schemas.common import PaginatedResponse
from app.schemas.public import PublicUserProfileResponse
from app.services.public_service import PublicService

router = APIRouter()


@router.get("/users/{username}", response_model=PublicUserProfileResponse)
def public_profile(username: str, db: Session = Depends(get_db)) -> PublicUserProfileResponse:
    return PublicService(db).profile(username=username)


@router.get("/users/{username}/collections", response_model=PaginatedResponse)
def public_collections(
    username: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: CollectionStatus | None = Query(default=None, alias="status"),
    language_code: str = Depends(get_language_code),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    return PublicService(db).collections(
        username=username,
        page=page,
        page_size=page_size,
        status=status_filter,
        language_code=language_code,
    )


@router.get("/users/{username}/favorites", response_model=PaginatedResponse)
def public_favorites(
    username: str,
    language_code: str = Depends(get_language_code),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    return PublicService(db).favorites(username=username, language_code=language_code)

