"""leituras

Revision ID: a3f1c2d4b5e6
Revises: e7ca9ef66b9e
Create Date: 2026-10-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f1c2d4b5e6'
down_revision: Union[str, None] = 'e7ca9ef66b9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('leituras',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hidrometro_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('litros_acumulados', sa.Float(), nullable=False),
    sa.Column('vazao_instantanea', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['hidrometro_id'], ['hidrometros.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('hidrometro_id', 'timestamp')
    )


def downgrade() -> None:
    op.drop_table('leituras')
