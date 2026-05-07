"""add anime genres json

Revision ID: 20260409_0002
Revises: 20260409_0001
Create Date: 2026-04-09 01:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260409_0002"
down_revision: Union[str, None] = "20260409_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("anime", sa.Column("genres_json", sa.Text(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("anime", "genres_json")
