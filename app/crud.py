"""Blog post storage (posts table)."""
import re
import unicodedata
from datetime import datetime
from typing import List, Optional

from app.db_models import PostRow
from app.models import Post, PostCreate, PostUpdate
from app.storage import Database, table


def _posts(db: Database):
    return table(db, PostRow)


def _to_post(row: dict) -> Post:
    return Post(
        id=str(row["id"]),
        slug=row["slug"],
        title=row["title"],
        content=row["content"],
        excerpt=row["excerpt"],
        tags=row["tags"] or [],
        date=row["date"],
    )


def _generate_slug(title: str) -> str:
    """URL-friendly slug: lowercase ASCII words joined by hyphens.

    Accents are dropped ("Por qué" -> "por-que") and other punctuation is
    removed ("Test: Post @2024 (Important!)" -> "test-post-2024-important").
    """
    slug = unicodedata.normalize("NFKD", title.lower()).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    # A title with no letters or digits (e.g. only emoji) still needs a slug
    return slug or "post"


def get_post(db: Database, slug: str) -> Optional[Post]:
    """Get a single post by slug"""
    row = _posts(db).get(slug=slug)
    return _to_post(row) if row else None


def get_post_by_id(db: Database, post_id: str) -> Optional[Post]:
    """Get a single post by its id"""
    if not post_id.isdigit():
        return None
    row = _posts(db).get(id=int(post_id))
    return _to_post(row) if row else None


def list_posts(
    db: Database,
    page: int = 1,
    limit: int = 10,
    tag: Optional[str] = None,
) -> tuple[List[Post], int]:
    """List posts, newest first, with pagination and optional tag filtering"""
    posts = [_to_post(row) for row in _posts(db).all()]
    # Sorting, filtering and paging happen here rather than in the database so
    # both backends behave the same; fine at blog scale.
    posts.sort(key=lambda p: (p.date, int(p.id)), reverse=True)
    if tag:
        posts = [p for p in posts if tag in p.tags]

    total = len(posts)
    start = (page - 1) * limit
    return posts[start:start + limit], total


def create_post(db: Database, post: PostCreate) -> Post:
    """Create a new post"""
    posts = _posts(db)
    slug = _generate_slug(post.title)

    # Handle slug conflicts
    counter = 1
    original_slug = slug
    while posts.get(slug=slug):
        slug = f"{original_slug}-{counter}"
        counter += 1

    row = posts.insert({
        "slug": slug,
        "title": post.title,
        "content": post.content,
        "excerpt": post.excerpt or post.content[:100],
        "tags": post.tags,
        "date": datetime.now(),
    })
    return _to_post(row)


def update_post(db: Database, slug: str, post_update: PostUpdate) -> Optional[Post]:
    """Update an existing post; only fields that are sent are changed"""
    row = _posts(db).update(post_update.model_dump(exclude_none=True), slug=slug)
    return _to_post(row) if row else None


def delete_post(db: Database, slug: str) -> bool:
    """Delete a post by slug"""
    return _posts(db).delete(slug=slug)
