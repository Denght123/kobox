from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_id, get_language_code
from app.db.session import get_db
from app.models.user import User
from app.models.user_collection import CollectionStatus
from app.schemas.collection import CollectionCreateRequest, CollectionItem, CollectionUpdateRequest
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.collection_service import CollectionService

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def list_collections(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: CollectionStatus | None = Query(default=None, alias="status"),
    include_total: bool = Query(default=True),
    language_code: str = Depends(get_language_code),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    return CollectionService(db).list_collections(
        user_id=current_user_id,
        page=page,
        page_size=page_size,
        status=status_filter,
        language_code=language_code,
        include_total=include_total,
    )


@router.post("", response_model=CollectionItem, status_code=status.HTTP_201_CREATED)
def add_collection(
    payload: CollectionCreateRequest,
    language_code: str = Depends(get_language_code),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CollectionItem:
    return CollectionService(db).add_collection(user=current_user, payload=payload, language_code=language_code)


@router.put("/{collection_id}", response_model=CollectionItem)
def update_collection(
    collection_id: int,
    payload: CollectionUpdateRequest,
    language_code: str = Depends(get_language_code),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CollectionItem:
    return CollectionService(db).update_collection(
        user=current_user,
        collection_id=collection_id,
        payload=payload,
        language_code=language_code,
    )


@router.delete("/{collection_id}", response_model=MessageResponse)
def delete_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    return MessageResponse(**CollectionService(db).delete_collection(user=current_user, collection_id=collection_id))
