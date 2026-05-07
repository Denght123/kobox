"""initial schema

Revision ID: 20260409_0001
Revises:
Create Date: 2026-04-09 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260409_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


collection_status_enum = sa.Enum(
    "completed",
    "watching",
    "plan_to_watch",
    "on_hold",
    "dropped",
    name="collection_status_enum",
)


def upgrade() -> None:
    op.create_table(
        "anime",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("cover_url", sa.String(length=500), nullable=False),
        sa.Column("source_cover_url", sa.String(length=500), nullable=True),
        sa.Column("local_cover_url", sa.String(length=500), nullable=True),
        sa.Column("cover_source", sa.String(length=64), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("season", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "anime_translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("anime_id", sa.Integer(), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["anime_id"], ["anime.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("anime_id", "language_code", name="uq_anime_language"),
    )
    op.create_index(op.f("ix_anime_translations_anime_id"), "anime_translations", ["anime_id"], unique=False)
    op.create_index(op.f("ix_anime_translations_title"), "anime_translations", ["title"], unique=False)

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("birthday", sa.Date(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("public_slug", sa.String(length=128), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="zh-CN"),
        sa.Column("show_dynamic_background", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("show_public_rank", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_slug"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_profiles_public_slug"), "user_profiles", ["public_slug"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_jti"),
    )
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_token_jti"), "refresh_tokens", ["token_jti"], unique=True)

    op.create_table(
        "user_collections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("anime_id", sa.Integer(), nullable=False),
        sa.Column("collection_status", collection_status_enum, nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["anime_id"], ["anime.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "anime_id", name="uq_user_collection_anime"),
    )
    op.create_index(op.f("ix_user_collections_user_id"), "user_collections", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_collections_anime_id"), "user_collections", ["anime_id"], unique=False)

    op.create_table(
        "user_favorite_ranks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("anime_id", sa.Integer(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["anime_id"], ["anime.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "anime_id", name="uq_user_favorite_anime"),
        sa.UniqueConstraint("user_id", "rank_order", name="uq_user_favorite_rank_order"),
    )
    op.create_index(op.f("ix_user_favorite_ranks_user_id"), "user_favorite_ranks", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_favorite_ranks_anime_id"), "user_favorite_ranks", ["anime_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_favorite_ranks_anime_id"), table_name="user_favorite_ranks")
    op.drop_index(op.f("ix_user_favorite_ranks_user_id"), table_name="user_favorite_ranks")
    op.drop_table("user_favorite_ranks")

    op.drop_index(op.f("ix_user_collections_anime_id"), table_name="user_collections")
    op.drop_index(op.f("ix_user_collections_user_id"), table_name="user_collections")
    op.drop_table("user_collections")

    op.drop_index(op.f("ix_refresh_tokens_token_jti"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index(op.f("ix_user_profiles_public_slug"), table_name="user_profiles")
    op.drop_table("user_profiles")

    op.drop_index(op.f("ix_anime_translations_title"), table_name="anime_translations")
    op.drop_index(op.f("ix_anime_translations_anime_id"), table_name="anime_translations")
    op.drop_table("anime_translations")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")

    op.drop_table("anime")

    collection_status_enum.drop(op.get_bind(), checkfirst=False)
