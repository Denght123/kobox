from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_id, get_language_code
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    AvatarUploadResponse,
    BackgroundUploadResponse,
    UserDashboardResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserSettingsResponse,
    UserSettingsUpdateRequest,
)
from app.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=UserProfileResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    return UserService(db).get_me(current_user)


@router.get("/dashboard", response_model=UserDashboardResponse)
def get_dashboard(
    current_user_id: int = Depends(get_current_user_id),
    language_code: str = Depends(get_language_code),
    db: Session = Depends(get_db),
) -> UserDashboardResponse:
    return UserService(db).get_dashboard_by_user_id(current_user_id, language_code=language_code)


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    return UserService(db).update_profile(current_user, payload)


@router.get("/settings", response_model=UserSettingsResponse)
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserSettingsResponse:
    return UserService(db).get_settings(current_user)


@router.put("/settings", response_model=UserSettingsResponse)
def update_settings(
    payload: UserSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserSettingsResponse:
    return UserService(db).update_settings(current_user, payload)


@router.post("/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AvatarUploadResponse:
    return await UserService(db).upload_avatar(
        user=current_user,
        file=file,
        request_base_url=str(request.base_url),
    )


@router.post("/background", response_model=BackgroundUploadResponse)
async def upload_background(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BackgroundUploadResponse:
    return await UserService(db).upload_background(
        user=current_user,
        file=file,
        request_base_url=str(request.base_url),
    )


@router.delete("/background", response_model=BackgroundUploadResponse)
def clear_background(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BackgroundUploadResponse:
    return UserService(db).clear_background(current_user)
