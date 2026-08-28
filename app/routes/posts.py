from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models import Post, PostCreate, PostUpdate, PostListResponse

router = APIRouter(prefix="/posts", tags=["posts"])

# TODO: Replace with database queries
MOCK_POSTS = {
    "first-post": {
        "id": "1",
        "slug": "first-post",
        "title": "Welcome to My Blog",
        "content": "This is the first blog post...",
        "excerpt": "Welcome to agustinenriquez.dev",
        "tags": ["welcome", "intro"],
        "date": "2026-08-28T00:00:00"
    }
}


@router.get("", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    tag: Optional[str] = None
):
    """List all blog posts with pagination and filtering"""
    # TODO: Implement database pagination
    posts = list(MOCK_POSTS.values())

    if tag:
        posts = [p for p in posts if tag in p["tags"]]

    total = len(posts)
    start = (page - 1) * limit
    end = start + limit
    paginated = posts[start:end]

    return PostListResponse(
        posts=paginated,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{slug}", response_model=Post)
async def get_post(slug: str):
    """Get a single blog post by slug"""
    if slug not in MOCK_POSTS:
        raise HTTPException(status_code=404, detail="Post not found")
    return MOCK_POSTS[slug]


@router.post("", response_model=Post)
async def create_post(post: PostCreate):
    """Create a new blog post (admin only)"""
    # TODO: Add authentication check
    # TODO: Implement database storage
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{slug}", response_model=Post)
async def update_post(slug: str, post: PostUpdate):
    """Update a blog post (admin only)"""
    # TODO: Add authentication check
    # TODO: Implement database update
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{slug}")
async def delete_post(slug: str):
    """Delete a blog post (admin only)"""
    # TODO: Add authentication check
    # TODO: Implement database deletion
    raise HTTPException(status_code=501, detail="Not implemented")
