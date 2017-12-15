"""drop uncompressed content

Revision ID: 65f837e88667
Revises: 7f4065c8cbef
Create Date: 2017-12-15 15:15:08.158937

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '65f837e88667'
down_revision = '7f4065c8cbef'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('pages', 'content')
    op.alter_column('pages', 'content_compressed', new_column_name='content')


def downgrade():
    raise Exception("boi ur still not going back.")
