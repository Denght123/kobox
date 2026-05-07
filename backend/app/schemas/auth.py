from datetime import date

from pydantic import AliasChoices, BaseModel, EmailStr, Field

from app.schemas.user import UserDashboardResponse


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=128)


class LoginRequest(BaseModel):
    account: str = Field(validation_alias=AliasChoices("account", "email_or_username"))
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=16, max_length=256)
    password: str = Field(min_length=8, max_length=128)


class PasswordResetRequestResponse(BaseModel):
    message: str
    dev_reset_token: str | None = None


class AuthUser(BaseModel):
    id: int
    username: str
    public_slug: str
    display_name: str
    avatar_url: str | None = None
    background_image_url: str | None = None
    birthday: date | None = None
    bio: str | None = None
    is_public: bool


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: AuthUser
    dashboard: UserDashboardResponse | None = None
