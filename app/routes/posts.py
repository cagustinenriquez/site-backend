from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from app.models import Post, PostCreate, PostUpdate, PostListResponse
from app import crud
from app.auth import get_current_user

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    tag: Optional[str] = None
):
    """List all blog posts with pagination and filtering"""
    posts, total = crud.list_posts(page=page, limit=limit, tag=tag)

    return PostListResponse(
        posts=posts,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{slug}", response_model=Post)
async def get_post(slug: str):
    """Get a single blog post by slug"""
    post = crud.get_post(slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("", response_model=Post)
async def create_post(post: PostCreate, current_user: str = Depends(get_current_user)):
    """Create a new blog post (requires authentication)"""
    return crud.create_post(post)


@router.put("/{slug}", response_model=Post)
async def update_post(
    slug: str,
    post_update: PostUpdate,
    current_user: str = Depends(get_current_user)
):
    """Update a blog post (requires authentication)"""
    updated = crud.update_post(slug, post_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")
    return updated


@router.delete("/{slug}")
async def delete_post(slug: str, current_user: str = Depends(get_current_user)):
    """Delete a blog post (requires authentication)"""
    if not crud.delete_post(slug):
        raise HTTPException(status_code=404, detail="Post not found")
    return {"detail": "Post deleted successfully"}
