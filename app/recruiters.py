"""Recruiter storage (recruiters table)."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db_models import RecruiterRow
from app.models import Recruiter, RecruiterCreate, RecruiterSort, RecruiterUpdate


def _to_recruiter(row: RecruiterRow) -> Recruiter:
    return Recruiter(
        id=str(row.id),
        name=row.name,
        company=row.company,
        email=row.email,
        phone=row.phone,
        linkedin=row.linkedin,
        notes=row.notes,
        reputation=row.reputation,
        total_placements=row.total_placements,
        average_rating=row.average_rating,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _get_row(db: Session, recruiter_id: str) -> Optional[RecruiterRow]:
    if not recruiter_id.isdigit():
        return None
    return db.get(RecruiterRow, int(recruiter_id))


def get_recruiter(db: Session, recruiter_id: str) -> Optional[Recruiter]:
    row = _get_row(db, recruiter_id)
    return _to_recruiter(row) if row else None


def list_recruiters(
    db: Session,
    page: int = 1,
    limit: int = 10,
    sort: RecruiterSort = "reputation",
    search: Optional[str] = None,
) -> tuple[List[Recruiter], int]:
    query = select(RecruiterRow)
    if search:
        term = f"%{search}%"
        query = query.where(or_(RecruiterRow.name.ilike(term), RecruiterRow.company.ilike(term)))

    total = db.scalar(select(func.count()).select_from(query.subquery()))

    by_name = func.lower(RecruiterRow.name)
    if sort == "name":
        query = query.order_by(by_name, RecruiterRow.id)
    else:
        # Highest first; ties broken by name so paging is stable
        query = query.order_by(getattr(RecruiterRow, sort).desc(), by_name, RecruiterRow.id)

    rows = db.scalars(query.offset((page - 1) * limit).limit(limit)).all()
    return [_to_recruiter(row) for row in rows], total


def create_recruiter(db: Session, payload: RecruiterCreate) -> Recruiter:
    now = datetime.now()
    row = RecruiterRow(**payload.model_dump(), created_at=now, updated_at=now)
    db.add(row)
    db.commit()
    return _to_recruiter(row)


def update_recruiter(
    db: Session, recruiter_id: str, payload: RecruiterUpdate
) -> Optional[Recruiter]:
    row = _get_row(db, recruiter_id)
    if not row:
        return None
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    row.updated_at = datetime.now()
    db.commit()
    return _to_recruiter(row)


def delete_recruiter(db: Session, recruiter_id: str) -> bool:
    row = _get_row(db, recruiter_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
