from pydantic import BaseModel, Field, StringConstraints
from datetime import datetime
from typing import Annotated, List, Literal, Optional


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


class RecruiterCommentCreate(BaseModel):
    # Trimmed before the length check, so whitespace-only bodies are rejected
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class RecruiterComment(BaseModel):
    id: str
    recruiter_id: str
    author: str
    body: str
    created_at: datetime


InterviewType = Literal["coding", "system_design", "behavioral", "take_home", "pair_programming", "other"]
InterviewerSort = Literal["rating", "name", "created_at"]


class InterviewerBase(BaseModel):
    name: str = Field(min_length=1)
    company: str = Field(min_length=1)
    role: Optional[str] = None
    # The admin form sends "" when left blank
    email: str = ""
    linkedin: Optional[str] = None
    notes: Optional[str] = None
    interview_types: List[InterviewType] = []
    rating: float = Field(default=0.0, ge=0, le=5)


class InterviewerCreate(InterviewerBase):
    pass


class InterviewerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    company: Optional[str] = Field(default=None, min_length=1)
    role: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    notes: Optional[str] = None
    interview_types: Optional[List[InterviewType]] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)


class Interviewer(InterviewerBase):
    id: str
    created_at: datetime
    updated_at: datetime


class InterviewerListResponse(BaseModel):
    interviewers: List[Interviewer]
    total: int
    page: int
    limit: int


class InterviewerComment(BaseModel):
    id: str
    interviewer_id: str
    author: str
    body: str
    created_at: datetime
