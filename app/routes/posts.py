from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from app.models import Post, PostCreate, PostUpdate, PostListResponse
from app import crud
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.db import get_db

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostListResponse)
def list_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all blog posts with pagination and filtering"""
    posts, total = crud.list_posts(db, page=page, limit=limit, tag=tag)

    return PostListResponse(
        posts=posts,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/id/{post_id}", response_model=Post)
def get_post_by_id(post_id: str, db: Session = Depends(get_db)):
    """Get a single blog post by id"""
    post = crud.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("/{slug}", response_model=Post)
def get_post(slug: str, db: Session = Depends(get_db)):
    """Get a single blog post by slug"""
    post = crud.get_post(db, slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("", response_model=Post)
def create_post(
    post: PostCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new blog post (requires authentication)"""
    return crud.create_post(db, post)


@router.put("/{slug}", response_model=Post)
def update_post(
    slug: str,
    post_update: PostUpdate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a blog post (requires authentication)"""
    updated = crud.update_post(db, slug, post_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")
    return updated


@router.delete("/{slug}")
def delete_post(
    slug: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a blog post (requires authentication)"""
    if not crud.delete_post(db, slug):
        raise HTTPException(status_code=404, detail="Post not found")
    return {"detail": "Post deleted successfully"}
