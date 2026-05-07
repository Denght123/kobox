"""add anime is adult flag

Revision ID: 20260409_0003
Revises: 20260409_0002
Create Date: 2026-04-09 02:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260409_0003"
down_revision: Union[str, None] = "20260409_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "anime",
        sa.Column("is_adult", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("anime", "is_adult")
