"""Recruiter storage (recruiters table)."""
from datetime import datetime
from typing import List, Optional

from app.db_models import RecruiterRow
from app.models import Recruiter, RecruiterCreate, RecruiterSort, RecruiterUpdate
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
