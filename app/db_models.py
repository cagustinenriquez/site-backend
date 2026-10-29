"""Database tables. API request/response shapes live in app/models.py."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PostRow(Base):
    __tablename__ = "posts"
    # Never reuse ids of deleted rows (Postgres sequences already behave this way)
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)


class UserRow(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(150), primary_key=True)
    hashed_password: Mapped[str] = mapped_column(String(255))


class RecruiterRow(Base):
    __tablename__ = "recruiters"
    # Never reuse ids of deleted rows (Postgres sequences already behave this way)
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[Optional[str]] = mapped_column(String(100))
    linkedin: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    reputation: Mapped[int] = mapped_column(Integer, default=0)
    total_placements: Mapped[int] = mapped_column(Integer, default=0)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
