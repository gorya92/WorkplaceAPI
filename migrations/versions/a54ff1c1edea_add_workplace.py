"""add workplace

Revision ID: a54ff1c1edea
Revises: 40460b08b470
Create Date: 2024-05-21 14:06:51.417860

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a54ff1c1edea'
down_revision: Union[str, None] = '40460b08b470'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('workplace',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('max_people', sa.Integer(), nullable=False),
    sa.Column('current_people', sa.Integer(), nullable=True),
    sa.Column('camera_url', sa.String(), nullable=False),
    sa.Column('green_zone_coordinates', sa.JSON(), nullable=True),
    sa.Column('red_zone_coordinates', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_workplace',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('workplace_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['workplace_id'], ['workplace.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'workplace_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_workplace')
    op.drop_table('workplace')
    # ### end Alembic commands ###
