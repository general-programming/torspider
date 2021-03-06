"""onion list model

Revision ID: da7d39075bca
Revises: 65f837e88667
Create Date: 2018-01-01 21:49:27.681210

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da7d39075bca'
down_revision = '65f837e88667'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('onionlist_pages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('first_crawl', sa.DateTime(), nullable=False),
    sa.Column('last_crawl', sa.DateTime(), nullable=False),
    sa.Column('content', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('onionlist_pages')
    # ### end Alembic commands ###
