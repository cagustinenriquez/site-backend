from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app import interviewers as store
from app.auth import get_current_user
from app.db import get_db
from app.models import (
    Interviewer,
    InterviewerComment,
    InterviewerCreate,
    InterviewerListResponse,
    InterviewerSort,
    InterviewerUpdate,
    InterviewType,
    RecruiterCommentCreate,
)
from app.storage import Database

router = APIRouter(prefix="/interviewers", tags=["interviewers"])


@router.get("", response_model=InterviewerListResponse)
def list_interviewers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: InterviewerSort = "rating",
    search: Optional[str] = None,
    type: Optional[InterviewType] = None,
    current_user: str = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """List interviewers, sorted and optionally searched by name, company or role,
    or filtered by interview type (requires authentication)"""
    interviewers, total = store.list_interviewers(
        db, page=page, limit=limit, sort=sort, search=search, interview_type=type
    )
    return InterviewerListResponse(interviewers=interviewers, total=total, page=page, limit=limit)


@router.get("/{interviewer_id}", response_model=Interviewer)
def get_interviewer(
    interviewer_id: str,
    current_user: str = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Get one interviewer (requires authentication)"""
    interviewer = store.get_interviewer(db, interviewer_id)
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    return interviewer


@router.post("", response_model=Interviewer)
def create_interviewer(
    payload: InterviewerCreate,
    current_user: str = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Add an interviewer (requires authentication)"""
    return store.create_interviewer(db, payload)


@router.put("/{interviewer_id}", response_model=Interviewer)
def update_interviewer(
    interviewer_id: str,
    payload: InterviewerUpdate,
    current_user: str = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Update an interviewer (requires authentication)"""
    interviewer = store.update_interviewer(db, interviewer_id, payload)
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    return interviewer


@router.delete("/{interviewer_id}")
def delete_interviewer(
    interviewer_id: str,
    current_user: str = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Delete an interviewer and their comments (requires authentication)"""
    if not store.delete_interviewer(db, interviewer_id):
        raise HTTPException(status_code=404, detail="Interviewer not found")
    return {"detail": "Interviewer deleted successfully"}


@router.get("/{interviewer_id}/comments", response_model=List[InterviewerComment])
def list_comments(
    interviewer_id: str,
    current_user: str = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """An interviewer's comments, newest first (requires authentication)"""
    comments = store.list_comments(db, interviewer_id)
    if comments is None:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    return comments


@router.post("/{interviewer_id}/comments", response_model=InterviewerComment)
def add_comment(
    interviewer_id: str,
    payload: RecruiterCommentCreate,
    current_user: str = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Comment on an interviewer as the logged-in user (requires authentication)"""
    comment = store.add_comment(db, interviewer_id, current_user, payload)
    if comment is None:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    return comment


@router.delete("/{interviewer_id}/comments/{comment_id}")
def delete_comment(
    interviewer_id: str,
    comment_id: str,
    current_user: str = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Delete a comment (requires authentication)"""
    if not store.delete_comment(db, interviewer_id, comment_id):
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"detail": "Comment deleted successfully"}
