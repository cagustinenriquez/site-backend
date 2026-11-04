"""add recruiter_comments table

Revision ID: cf898baf8056
Revises: d03afa100f13
Create Date: 2026-11-04 11:27:47.652804

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf898baf8056'
down_revision: Union[str, None] = 'd03afa100f13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('recruiter_comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('recruiter_id', sa.Integer(), nullable=False),
    sa.Column('author', sa.String(length=150), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['recruiter_id'], ['recruiters.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sqlite_autoincrement=True
    )
    with op.batch_alter_table('recruiter_comments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_recruiter_comments_recruiter_id'), ['recruiter_id'], unique=False)

    # Same as the other tables: keep Supabase's public REST API (anon key) out
    if op.get_bind().dialect.name == "postgresql":
        op.execute('ALTER TABLE "recruiter_comments" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    with op.batch_alter_table('recruiter_comments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_recruiter_comments_recruiter_id'))

    op.drop_table('recruiter_comments')
