"""Technical interviewer storage (interviewers and interviewer_comments tables)."""
from datetime import datetime
from typing import List, Optional

from app.db_models import InterviewerCommentRow, InterviewerRow
from app.models import (
    Interviewer,
    InterviewerComment,
    InterviewerCreate,
    InterviewerSort,
    InterviewerUpdate,
    InterviewType,
    RecruiterCommentCreate,
)
from app.storage import Database, table


def _interviewers(db: Database):
    return table(db, InterviewerRow)


def _to_interviewer(row: dict) -> Interviewer:
    return Interviewer(**{**row, "id": str(row["id"]), "interview_types": row["interview_types"] or []})


def get_interviewer(db: Database, interviewer_id: str) -> Optional[Interviewer]:
    if not interviewer_id.isdigit():
        return None
    row = _interviewers(db).get(id=int(interviewer_id))
    return _to_interviewer(row) if row else None


def list_interviewers(
    db: Database,
    page: int = 1,
    limit: int = 10,
    sort: InterviewerSort = "rating",
    search: Optional[str] = None,
    interview_type: Optional[InterviewType] = None,
) -> tuple[List[Interviewer], int]:
    # Filtered and sorted here rather than in the query, so both backends behave the same
    interviewers = [_to_interviewer(row) for row in _interviewers(db).all()]

    if search:
        term = search.lower()
        interviewers = [
            i for i in interviewers
            if term in i.name.lower() or term in i.company.lower() or term in (i.role or "").lower()
        ]

    if interview_type:
        interviewers = [i for i in interviewers if interview_type in i.interview_types]

    # Ties broken by name, then id, so paging is stable
    if sort == "name":
        interviewers.sort(key=lambda i: (i.name.lower(), int(i.id)))
    else:
        # created_at: newest first; rating: highest first
        interviewers.sort(key=lambda i: (i.name.lower(), int(i.id)))
        interviewers.sort(key=lambda i: getattr(i, sort), reverse=True)

    total = len(interviewers)
    start = (page - 1) * limit
    return interviewers[start:start + limit], total


def create_interviewer(db: Database, payload: InterviewerCreate) -> Interviewer:
    now = datetime.now()
    # Every column sent explicitly (rating included, as given): column defaults
    # only exist in SQLAlchemy, so over Supabase's REST API they'd arrive as null
    row = _interviewers(db).insert({**payload.model_dump(), "created_at": now, "updated_at": now})
    return _to_interviewer(row)


def update_interviewer(
    db: Database, interviewer_id: str, payload: InterviewerUpdate
) -> Optional[Interviewer]:
    if not interviewer_id.isdigit():
        return None
    values = {**payload.model_dump(exclude_none=True), "updated_at": datetime.now()}
    row = _interviewers(db).update(values, id=int(interviewer_id))
    return _to_interviewer(row) if row else None


def delete_interviewer(db: Database, interviewer_id: str) -> bool:
    if not interviewer_id.isdigit():
        return False
    return _interviewers(db).delete(id=int(interviewer_id))


def _comments(db: Database):
    return table(db, InterviewerCommentRow)


def _to_comment(row: dict) -> InterviewerComment:
    return InterviewerComment(
        **{**row, "id": str(row["id"]), "interviewer_id": str(row["interviewer_id"])}
    )


def _interviewer_exists(db: Database, interviewer_id: str) -> bool:
    return interviewer_id.isdigit() and _interviewers(db).get(id=int(interviewer_id)) is not None


def list_comments(db: Database, interviewer_id: str) -> Optional[List[InterviewerComment]]:
    """An interviewer's comments, newest first; None if the interviewer doesn't exist"""
    if not _interviewer_exists(db, interviewer_id):
        return None
    comments = [_to_comment(row) for row in _comments(db).all(interviewer_id=int(interviewer_id))]
    comments.sort(key=lambda c: (c.created_at, int(c.id)), reverse=True)
    return comments


def add_comment(
    db: Database, interviewer_id: str, author: str, payload: RecruiterCommentCreate
) -> Optional[InterviewerComment]:
    """None if the interviewer doesn't exist"""
    if not _interviewer_exists(db, interviewer_id):
        return None
    row = _comments(db).insert({
        "interviewer_id": int(interviewer_id),
        "author": author,
        "body": payload.body,
        "created_at": datetime.now(),
    })
    return _to_comment(row)


def delete_comment(db: Database, interviewer_id: str, comment_id: str) -> bool:
    """Only deletes the comment if it belongs to this interviewer"""
    if not (interviewer_id.isdigit() and comment_id.isdigit()):
        return False
    return _comments(db).delete(id=int(comment_id), interviewer_id=int(interviewer_id))
