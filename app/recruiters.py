"""Recruiter storage (recruiters table)."""
from datetime import datetime
from typing import List, Optional

from app.db_models import RecruiterCommentRow, RecruiterRow
from app.models import (
    Recruiter,
    RecruiterComment,
    RecruiterCommentCreate,
    RecruiterCreate,
    RecruiterSort,
    RecruiterUpdate,
)
from app.storage import Database, table


def _recruiters(db: Database):
    return table(db, RecruiterRow)


def _to_recruiter(row: dict) -> Recruiter:
    return Recruiter(**{**row, "id": str(row["id"])})


def get_recruiter(db: Database, recruiter_id: str) -> Optional[Recruiter]:
    if not recruiter_id.isdigit():
        return None
    row = _recruiters(db).get(id=int(recruiter_id))
    return _to_recruiter(row) if row else None


def list_recruiters(
    db: Database,
    page: int = 1,
    limit: int = 10,
    sort: RecruiterSort = "reputation",
    search: Optional[str] = None,
) -> tuple[List[Recruiter], int]:
    recruiters = [_to_recruiter(row) for row in _recruiters(db).all()]

    if search:
        term = search.lower()
        recruiters = [
            r for r in recruiters
            if term in r.name.lower() or term in r.company.lower()
        ]

    if sort == "name":
        recruiters.sort(key=lambda r: (r.name.lower(), int(r.id)))
    else:
        # Highest first; ties broken by name so paging is stable
        recruiters.sort(key=lambda r: (-getattr(r, sort), r.name.lower(), int(r.id)))

    total = len(recruiters)
    start = (page - 1) * limit
    return recruiters[start:start + limit], total


def create_recruiter(db: Database, payload: RecruiterCreate) -> Recruiter:
    now = datetime.now()
    row = _recruiters(db).insert({
        **payload.model_dump(),
        # Explicit, not left to column defaults: those only exist in SQLAlchemy,
        # so over Supabase's REST API they'd arrive as null
        "total_placements": 0,
        "average_rating": 0.0,
        "created_at": now,
        "updated_at": now,
    })
    return _to_recruiter(row)


def update_recruiter(
    db: Database, recruiter_id: str, payload: RecruiterUpdate
) -> Optional[Recruiter]:
    if not recruiter_id.isdigit():
        return None
    values = {**payload.model_dump(exclude_none=True), "updated_at": datetime.now()}
    row = _recruiters(db).update(values, id=int(recruiter_id))
    return _to_recruiter(row) if row else None


def delete_recruiter(db: Database, recruiter_id: str) -> bool:
    if not recruiter_id.isdigit():
        return False
    return _recruiters(db).delete(id=int(recruiter_id))


def _comments(db: Database):
    return table(db, RecruiterCommentRow)


def _to_comment(row: dict) -> RecruiterComment:
    return RecruiterComment(**{**row, "id": str(row["id"]), "recruiter_id": str(row["recruiter_id"])})


def _recruiter_exists(db: Database, recruiter_id: str) -> bool:
    return recruiter_id.isdigit() and _recruiters(db).get(id=int(recruiter_id)) is not None


def list_comments(db: Database, recruiter_id: str) -> Optional[List[RecruiterComment]]:
    """A recruiter's comments, newest first; None if the recruiter doesn't exist"""
    if not _recruiter_exists(db, recruiter_id):
        return None
    comments = [_to_comment(row) for row in _comments(db).all(recruiter_id=int(recruiter_id))]
    comments.sort(key=lambda c: (c.created_at, int(c.id)), reverse=True)
    return comments


def add_comment(
    db: Database, recruiter_id: str, author: str, payload: RecruiterCommentCreate
) -> Optional[RecruiterComment]:
    """None if the recruiter doesn't exist"""
    if not _recruiter_exists(db, recruiter_id):
        return None
    row = _comments(db).insert({
        "recruiter_id": int(recruiter_id),
        "author": author,
        "body": payload.body,
        "created_at": datetime.now(),
    })
    return _to_comment(row)


def delete_comment(db: Database, recruiter_id: str, comment_id: str) -> bool:
    """Only deletes the comment if it belongs to this recruiter"""
    if not (recruiter_id.isdigit() and comment_id.isdigit()):
        return False
    return _comments(db).delete(id=int(comment_id), recruiter_id=int(recruiter_id))
