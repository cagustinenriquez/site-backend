"""add interviewers and interviewer_comments tables

Revision ID: 9de5c2019cd2
Revises: cf898baf8056
Create Date: 2026-11-05 11:20:00.072859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9de5c2019cd2'
down_revision: Union[str, None] = 'cf898baf8056'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('interviewers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('company', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('linkedin', sa.String(length=500), nullable=True),
    sa.Column('interview_types', sa.JSON(), nullable=False),
    sa.Column('rating', sa.Float(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sqlite_autoincrement=True
    )
    op.create_table('interviewer_comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('interviewer_id', sa.Integer(), nullable=False),
    sa.Column('author', sa.String(length=150), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['interviewer_id'], ['interviewers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sqlite_autoincrement=True
    )
    with op.batch_alter_table('interviewer_comments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interviewer_comments_interviewer_id'), ['interviewer_id'], unique=False)

    # Same as the other tables: keep Supabase's public REST API (anon key) out
    if op.get_bind().dialect.name == "postgresql":
        for table in ["interviewers", "interviewer_comments"]:
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    with op.batch_alter_table('interviewer_comments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interviewer_comments_interviewer_id'))

    op.drop_table('interviewer_comments')
    op.drop_table('interviewers')
