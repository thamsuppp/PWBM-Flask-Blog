"""empty message

Revision ID: 37356bfdda95
Revises: 
Create Date: 2019-07-02 11:00:27.974429

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '37356bfdda95'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_file', sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.drop_column('image_file')

    # ### end Alembic commands ###
