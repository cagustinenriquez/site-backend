"""create posts, users and recruiters tables

Revision ID: d03afa100f13
Revises: 
Create Date: 2026-10-29 11:49:27.475216

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd03afa100f13'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RLS_TABLES = ["posts", "recruiters", "users", "alembic_version"]


def upgrade() -> None:
    op.create_table('posts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=255), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('excerpt', sa.Text(), nullable=True),
    sa.Column('tags', sa.JSON(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sqlite_autoincrement=True
    )
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_posts_date'), ['date'], unique=False)
        batch_op.create_index(batch_op.f('ix_posts_slug'), ['slug'], unique=True)

    op.create_table('recruiters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('company', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=100), nullable=True),
    sa.Column('linkedin', sa.String(length=500), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('reputation', sa.Integer(), nullable=False),
    sa.Column('total_placements', sa.Integer(), nullable=False),
    sa.Column('average_rating', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sqlite_autoincrement=True
    )
    op.create_table('users',
    sa.Column('username', sa.String(length=150), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('username')
    )

    # Supabase exposes tables in the public schema through its REST API to
    # anyone holding the project's anon key. Turn on Row Level Security with
    # no policies so that API can't read or write these tables. The backend
    # connects as the table owner, which RLS doesn't apply to.
    if op.get_bind().dialect.name == "postgresql":
        for table in RLS_TABLES:
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    op.drop_table('users')
    op.drop_table('recruiters')
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_posts_slug'))
        batch_op.drop_index(batch_op.f('ix_posts_date'))

    op.drop_table('posts')
