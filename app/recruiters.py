"""File-based storage for recruiters (data/recruiters.json), keyed by id."""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.models import Recruiter, RecruiterCreate, RecruiterSort, RecruiterUpdate

RECRUITERS_FILE = Path("data") / "recruiters.json"


def _load() -> dict:
    if not RECRUITERS_FILE.exists():
        return {}
    with open(RECRUITERS_FILE, "r") as f:
        return json.load(f)


def _save(recruiters: dict):
    RECRUITERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RECRUITERS_FILE, "w") as f:
        json.dump(recruiters, f, indent=2)


def _next_id(recruiters: dict) -> str:
    ids = [int(k) for k in recruiters if k.isdigit()]
    return str(max(ids, default=0) + 1)


def get_recruiter(recruiter_id: str) -> Optional[Recruiter]:
    data = _load().get(recruiter_id)
    return Recruiter(**data) if data else None


def list_recruiters(
    page: int = 1,
    limit: int = 10,
    sort: RecruiterSort = "reputation",
    search: Optional[str] = None,
) -> tuple[List[Recruiter], int]:
    recruiters = [Recruiter(**data) for data in _load().values()]

    if search:
        term = search.lower()
        recruiters = [
            r for r in recruiters
            if term in r.name.lower() or term in r.company.lower()
        ]

    if sort == "name":
        recruiters.sort(key=lambda r: r.name.lower())
    else:
        # Highest first; ties broken by name so paging is stable
        recruiters.sort(key=lambda r: r.name.lower())
        recruiters.sort(key=lambda r: getattr(r, sort), reverse=True)

    total = len(recruiters)
    start = (page - 1) * limit
    return recruiters[start:start + limit], total


def create_recruiter(payload: RecruiterCreate) -> Recruiter:
    recruiters = _load()
    now = datetime.now()
    recruiter = Recruiter(
        id=_next_id(recruiters),
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    recruiters[recruiter.id] = recruiter.model_dump(mode="json")
    _save(recruiters)
    return recruiter


def update_recruiter(recruiter_id: str, payload: RecruiterUpdate) -> Optional[Recruiter]:
    recruiters = _load()
    if recruiter_id not in recruiters:
        return None
    data = recruiters[recruiter_id]
    data.update(payload.model_dump(exclude_none=True))
    data["updated_at"] = datetime.now().isoformat()
    recruiter = Recruiter(**data)
    recruiters[recruiter_id] = recruiter.model_dump(mode="json")
    _save(recruiters)
    return recruiter


def delete_recruiter(recruiter_id: str) -> bool:
    recruiters = _load()
    if recruiter_id not in recruiters:
        return False
    del recruiters[recruiter_id]
    _save(recruiters)
    return True
