from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_language_code
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.services.anime_service import AnimeService

router = APIRouter()


@router.get("/search", response_model=PaginatedResponse)
def search_anime(
    q: str = Query(min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    language_code: str = Depends(get_language_code),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    return AnimeService(db).search(query=q, page=page, page_size=page_size, language_code=language_code)


@router.get("/search/suggestions", response_model=PaginatedResponse)
def search_suggestions(
    q: str = Query(min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    language_code: str = Depends(get_language_code),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    return AnimeService(db).suggestions(query=q, page=page, page_size=page_size, language_code=language_code)
