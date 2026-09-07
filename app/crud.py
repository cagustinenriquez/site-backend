import json
import os
import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from app.models import Post, PostCreate, PostUpdate
from app.config import DATA_DIR

POSTS_FILE = DATA_DIR / "posts.json"


def _ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_posts() -> dict:
    """Load all posts from JSON file"""
    _ensure_data_dir()
    if not POSTS_FILE.exists():
        return {}

    with open(POSTS_FILE, "r") as f:
        return json.load(f)


def _save_posts(posts: dict):
    """Save posts to JSON file"""
    _ensure_data_dir()
    with open(POSTS_FILE, "w") as f:
        json.dump(posts, f, indent=2)


def _generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


def get_post(slug: str) -> Optional[Post]:
    """Get a single post by slug"""
    posts = _load_posts()
    post_data = posts.get(slug)
    if not post_data:
        return None
    return Post(**post_data)


def get_post_by_id(post_id: str) -> Optional[Post]:
    """Get a single post by ID"""
    posts = _load_posts()
    for post_data in posts.values():
        if post_data.get("id") == post_id:
            return Post(**post_data)
    return None


def list_posts(
    page: int = 1,
    limit: int = 10,
    tag: Optional[str] = None
) -> tuple[List[Post], int]:
    """List posts with pagination and optional tag filtering"""
    posts = _load_posts()
    posts_list = [Post(**data) for data in posts.values()]

    # Filter by tag if provided
    if tag:
        posts_list = [p for p in posts_list if tag in p.tags]

    # Sort by date descending
    posts_list.sort(key=lambda p: p.date, reverse=True)

    total = len(posts_list)
    start = (page - 1) * limit
    end = start + limit

    return posts_list[start:end], total


def create_post(post: PostCreate) -> Post:
    """Create a new post"""
    posts = _load_posts()

    slug = _generate_slug(post.title)

    # Handle slug conflicts
    counter = 1
    original_slug = slug
    while slug in posts:
        slug = f"{original_slug}-{counter}"
        counter += 1

    new_post = Post(
        id=str(len(posts) + 1),
        slug=slug,
        title=post.title,
        content=post.content,
        excerpt=post.excerpt or post.content[:100],
        tags=post.tags,
        date=datetime.now()
    )

    posts[slug] = new_post.model_dump()
    _save_posts(posts)

    return new_post


def update_post(slug: str, post_update: PostUpdate) -> Optional[Post]:
    """Update an existing post"""
    posts = _load_posts()

    if slug not in posts:
        return None

    post_data = posts[slug]

    # Update only provided fields
    if post_update.title is not None:
        post_data["title"] = post_update.title
    if post_update.content is not None:
        post_data["content"] = post_update.content
    if post_update.excerpt is not None:
        post_data["excerpt"] = post_update.excerpt
    if post_update.tags is not None:
        post_data["tags"] = post_update.tags

    posts[slug] = post_data
    _save_posts(posts)

    return Post(**post_data)


def delete_post(slug: str) -> bool:
    """Delete a post by slug"""
    posts = _load_posts()

    if slug not in posts:
        return False

    del posts[slug]
    _save_posts(posts)

    return True
