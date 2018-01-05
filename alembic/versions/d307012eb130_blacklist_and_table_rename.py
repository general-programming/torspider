"""blacklist and table rename

Revision ID: d307012eb130
Revises: 60f8471d8dcb
Create Date: 2018-01-02 14:09:12.189360

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd307012eb130'
down_revision = '60f8471d8dcb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('onion_blacklist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hexhash', sa.String(), nullable=False),
    sa.Column('source', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('index_blacklist_hash', 'onion_blacklist', ['hexhash'], unique=False)
    # ### end Alembic commands ###
    op.rename_table('onionlist_pages', 'onion_listpages')
    op.execute('ALTER SEQUENCE onionlist_pages_id_seq RENAME TO onion_listpages_id_seq')
    op.execute('ALTER INDEX onionlist_pages_pkey RENAME TO onion_listpages_pkey')


def downgrade():
    raise Exception("no goin back boi")