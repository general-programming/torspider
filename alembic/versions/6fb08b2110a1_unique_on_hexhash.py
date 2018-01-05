"""unique on hexhash

Revision ID: 6fb08b2110a1
Revises: 1c98a11a06db
Create Date: 2018-01-05 06:07:21.123933

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6fb08b2110a1'
down_revision = '1c98a11a06db'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'onion_blacklist', ['hexhash'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'onion_blacklist', type_='unique')
    # ### end Alembic commands ###
