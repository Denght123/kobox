"""add profile background image

Revision ID: 20260416_0006
Revises: 20260414_0005
Create Date: 2026-04-16 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260416_0006"
down_revision: Union[str, None] = "20260414_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("background_image_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("user_profiles", "background_image_url")
