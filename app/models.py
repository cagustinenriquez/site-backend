from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Literal, Optional


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


RecruiterSort = Literal["reputation", "total_placements", "average_rating", "name"]


class RecruiterBase(BaseModel):
    name: str = Field(min_length=1)
    company: str = Field(min_length=1)
    # Contact fields are optional; the admin form sends "" when left blank
    email: str = ""
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    notes: Optional[str] = None
    # Signed score: positive = good experience, negative = bad
    reputation: int = 0


class RecruiterCreate(RecruiterBase):
    pass


class RecruiterUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    company: Optional[str] = Field(default=None, min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    notes: Optional[str] = None
    reputation: Optional[int] = None
    total_placements: Optional[int] = Field(default=None, ge=0)
    average_rating: Optional[float] = Field(default=None, ge=0, le=5)


class Recruiter(RecruiterBase):
    id: str
    total_placements: int = 0
    average_rating: float = 0.0
    created_at: datetime
    updated_at: datetime


class RecruiterListResponse(BaseModel):
    recruiters: List[Recruiter]
    total: int
    page: int
    limit: int
