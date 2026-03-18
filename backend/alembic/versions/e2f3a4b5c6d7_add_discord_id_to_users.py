"""add discord_id to users

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-03-18 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2f3a4b5c6d7"
down_revision: str | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("discord_id", sa.String(), nullable=True))
    op.create_unique_constraint("uq_users_discord_id", "users", ["discord_id"])


def downgrade() -> None:
    op.drop_constraint("uq_users_discord_id", "users", type_="unique")
    op.drop_column("users", "discord_id")
