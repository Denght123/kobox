from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_id, get_language_code
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.favorite import FavoriteRankUpdateRequest
from app.services.favorite_service import FavoriteService

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def get_favorites(
    language_code: str = Depends(get_language_code),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    return FavoriteService(db).list_favorites(user_id=current_user_id, language_code=language_code)


@router.put("/rank", response_model=PaginatedResponse)
def update_favorites(
    payload: FavoriteRankUpdateRequest,
    language_code: str = Depends(get_language_code),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    return FavoriteService(db).replace_favorites(user=current_user, payload=payload, language_code=language_code)
