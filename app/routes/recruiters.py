from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import recruiters as store
from app.auth import get_current_user
from app.db import get_db
from app.models import (
    Recruiter,
    RecruiterCreate,
    RecruiterListResponse,
    RecruiterSort,
    RecruiterUpdate,
)

router = APIRouter(prefix="/recruiters", tags=["recruiters"])


@router.get("", response_model=RecruiterListResponse)
def list_recruiters(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: RecruiterSort = "reputation",
    search: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List recruiters, sorted (highest first) and optionally searched by name or company (requires authentication)"""
    recruiters, total = store.list_recruiters(db, page=page, limit=limit, sort=sort, search=search)
    return RecruiterListResponse(recruiters=recruiters, total=total, page=page, limit=limit)


@router.get("/{recruiter_id}", response_model=Recruiter)
def get_recruiter(
    recruiter_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get one recruiter (requires authentication)"""
    recruiter = store.get_recruiter(db, recruiter_id)
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    return recruiter


@router.post("", response_model=Recruiter)
def create_recruiter(
    payload: RecruiterCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a recruiter (requires authentication)"""
    return store.create_recruiter(db, payload)


@router.put("/{recruiter_id}", response_model=Recruiter)
def update_recruiter(
    recruiter_id: str,
    payload: RecruiterUpdate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a recruiter (requires authentication)"""
    recruiter = store.update_recruiter(db, recruiter_id, payload)
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    return recruiter


@router.delete("/{recruiter_id}")
def delete_recruiter(
    recruiter_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a recruiter (requires authentication)"""
    if not store.delete_recruiter(db, recruiter_id):
        raise HTTPException(status_code=404, detail="Recruiter not found")
    return {"detail": "Recruiter deleted successfully"}
