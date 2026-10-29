"""Blog post storage (posts table)."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import PostRow
from app.models import Post, PostCreate, PostUpdate


def _to_post(row: PostRow) -> Post:
    return Post(
        id=str(row.id),
        slug=row.slug,
        title=row.title,
        content=row.content,
        excerpt=row.excerpt,
        tags=row.tags or [],
        date=row.date,
    )


def _generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    return title.lower().replace(" ", "-").replace(".", "").replace(",", "")


def _get_row(db: Session, slug: str) -> Optional[PostRow]:
    return db.scalar(select(PostRow).where(PostRow.slug == slug))


def get_post(db: Session, slug: str) -> Optional[Post]:
    """Get a single post by slug"""
    row = _get_row(db, slug)
    return _to_post(row) if row else None


def list_posts(
    db: Session,
    page: int = 1,
    limit: int = 10,
    tag: Optional[str] = None,
) -> tuple[List[Post], int]:
    """List posts, newest first, with pagination and optional tag filtering"""
    rows = db.scalars(select(PostRow).order_by(PostRow.date.desc(), PostRow.id.desc())).all()
    posts = [_to_post(row) for row in rows]

    # Tags are a JSON list; filtering in Python keeps this portable across
    # SQLite and Postgres and is fine at blog scale.
    if tag:
        posts = [p for p in posts if tag in p.tags]

    total = len(posts)
    start = (page - 1) * limit
    return posts[start:start + limit], total


def create_post(db: Session, post: PostCreate) -> Post:
    """Create a new post"""
    slug = _generate_slug(post.title)

    # Handle slug conflicts
    counter = 1
    original_slug = slug
    while _get_row(db, slug):
        slug = f"{original_slug}-{counter}"
        counter += 1

    row = PostRow(
        slug=slug,
        title=post.title,
        content=post.content,
        excerpt=post.excerpt or post.content[:100],
        tags=post.tags,
        date=datetime.now(),
    )
    db.add(row)
    db.commit()
    return _to_post(row)


def update_post(db: Session, slug: str, post_update: PostUpdate) -> Optional[Post]:
    """Update an existing post; only fields that are sent are changed"""
    row = _get_row(db, slug)
    if not row:
        return None

    for field, value in post_update.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.commit()
    return _to_post(row)


def delete_post(db: Session, slug: str) -> bool:
    """Delete a post by slug"""
    row = _get_row(db, slug)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
