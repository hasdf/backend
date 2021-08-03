"""add theme property

Revision ID: 7e3e4e2ce682
Revises: 39128f82b57f
Create Date: 2021-07-31 13:42:24.640120

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e3e4e2ce682'
down_revision = '39128f82b57f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('map', sa.Column('theme', sa.Unicode(), default='bright'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('map', 'theme')
    # ### end Alembic commands ###
