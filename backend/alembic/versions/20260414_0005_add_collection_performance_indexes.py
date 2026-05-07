"""add collection performance indexes

Revision ID: 20260414_0005
Revises: 20260414_0004
Create Date: 2026-04-14 21:45:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260414_0005"
down_revision: Union[str, None] = "20260414_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_user_collections_user_status_added",
        "user_collections",
        ["user_id", "collection_status", "added_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_collections_user_added",
        "user_collections",
        ["user_id", "added_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_favorite_ranks_user_rank",
        "user_favorite_ranks",
        ["user_id", "rank_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_favorite_ranks_user_rank", table_name="user_favorite_ranks")
    op.drop_index("ix_user_collections_user_added", table_name="user_collections")
    op.drop_index("ix_user_collections_user_status_added", table_name="user_collections")
