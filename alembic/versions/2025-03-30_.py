"""

Revision ID: 5d98defdf3f9
Revises:
Create Date: 2025-03-30 14:17:27.504633

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '5d98defdf3f9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'users',
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('users_pkey')),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    # ### end Alembic commands ###
