"""add_status_field

Revision ID: e43de36b1073
Revises: c6ec243ca4ec
Create Date: 2025-06-19 18:30:30.362909

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e43de36b1073"
down_revision: Union[str, None] = "c6ec243ca4ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("orders", sa.Column("status", sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("orders", "status")
    # ### end Alembic commands ###
