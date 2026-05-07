from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.user import User
from app.models.user_profile import UserProfile


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _with_profile(self) -> Select[tuple[User]]:
        return select(User).options(joinedload(User.profile))

    def get_by_id(self, user_id: int) -> User | None:
        stmt = self._with_profile().where(User.id == user_id)
        return self.db.scalars(stmt).first()

    def get_by_email(self, email: str) -> User | None:
        stmt = self._with_profile().where(User.email == email)
        return self.db.scalars(stmt).first()

    def get_by_username(self, username: str) -> User | None:
        stmt = self._with_profile().where(User.username == username)
        return self.db.scalars(stmt).first()

    def get_by_identifier(self, identifier: str) -> User | None:
        stmt = self._with_profile().where(or_(User.email == identifier, User.username == identifier))
        return self.db.scalars(stmt).first()

    def get_by_public_slug(self, slug: str) -> User | None:
        stmt = self._with_profile().join(UserProfile).where(UserProfile.public_slug == slug)
        return self.db.scalars(stmt).first()

    def create(self, *, email: str, username: str, password_hash: str, display_name: str, public_slug: str) -> User:
        user = User(email=email, username=username, password_hash=password_hash, is_active=True)
        profile = UserProfile(display_name=display_name, public_slug=public_slug, is_public=True)
        user.profile = profile
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def update_profile(
        self,
        *,
        user: User,
        avatar_url: str | None = None,
        background_image_url: str | None = None,
        display_name: str | None = None,
        birthday=None,
        bio: str | None = None,
        is_public: bool | None = None,
    ) -> User:
        profile = user.profile
        if profile is None:
            profile = UserProfile(display_name=user.username, public_slug=user.username, is_public=True)
            user.profile = profile

        if avatar_url is not None:
            profile.avatar_url = avatar_url
        if background_image_url is not None:
            profile.background_image_url = background_image_url
        if display_name is not None:
            profile.display_name = display_name
        if birthday is not None:
            profile.birthday = birthday
        if bio is not None:
            profile.bio = bio
        if is_public is not None:
            profile.is_public = is_public

        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def update_settings(
        self,
        *,
        user: User,
        language: str | None = None,
        show_dynamic_background: bool | None = None,
        show_public_rank: bool | None = None,
    ) -> User:
        profile = user.profile
        if profile is None:
            profile = UserProfile(
                display_name=user.username,
                public_slug=user.username,
                is_public=True,
            )
            user.profile = profile

        if language is not None:
            profile.language = language
        if show_dynamic_background is not None:
            profile.show_dynamic_background = show_dynamic_background
        if show_public_rank is not None:
            profile.show_public_rank = show_public_rank

        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def clear_background_image(self, *, user: User) -> User:
        profile = user.profile
        if profile is None:
            profile = UserProfile(display_name=user.username, public_slug=user.username, is_public=True)
            user.profile = profile

        profile.background_image_url = None
        profile.show_dynamic_background = True
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user
