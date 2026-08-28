from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class PostBase(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    tags: List[str] = []


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    tags: Optional[List[str]] = None


class Post(PostBase):
    id: str
    slug: str
    date: datetime

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    posts: List[Post]
    total: int
    page: int
    limit: int
