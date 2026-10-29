#!/usr/bin/env python3
"""
Copy data from the old JSON files into the database (DATABASE_URL).

Usage:
    python scripts/import_json_data.py [data_dir]      # default: data/

Reads posts.json, users.json and recruiters.json if present. Rows that
were already imported (same post slug, username, or recruiter name +
company + created_at) are skipped, so it's safe to run more than once.
Old ids are kept when free; otherwise the database assigns a new one.
Run `alembic upgrade head` first. Needs a direct DATABASE_URL connection;
it won't run with SUPABASE_URL/SUPABASE_KEY.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select, text  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.db_models import PostRow, RecruiterRow, UserRow  # noqa: E402


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _date(value) -> datetime:
    return datetime.fromisoformat(value) if value else datetime.now()


def _int_id(value):
    return int(value) if str(value).isdigit() else None


def _free_id(db, model, value):
    """The old id if no row uses it yet, else None (the database picks one)"""
    rid = _int_id(value)
    return rid if rid is not None and db.get(model, rid) is None else None


def import_posts(db, data: dict, deferred: list) -> int:
    added = 0
    for slug, post in data.items():
        # Same slug = same post, already imported
        if db.scalar(select(PostRow).where(PostRow.slug == slug)):
            continue
        row = PostRow(
            id=_free_id(db, PostRow, post.get("id")),
            slug=slug,
            title=post["title"],
            content=post["content"],
            excerpt=post.get("excerpt"),
            tags=post.get("tags") or [],
            date=_date(post.get("date")),
        )
        _add(db, row, deferred)
        added += 1
    return added


def import_users(db, data: dict, deferred: list) -> int:
    added = 0
    for username, user in data.items():
        if db.get(UserRow, username):
            continue
        db.add(UserRow(username=username, hashed_password=user["hashed_password"]))
        db.flush()
        added += 1
    return added


def import_recruiters(db, data: dict, deferred: list) -> int:
    added = 0
    for key, r in data.items():
        created_at = _date(r.get("created_at"))
        # Same name, company and creation time = same recruiter, already imported
        if db.scalar(select(RecruiterRow).where(
            RecruiterRow.name == r["name"],
            RecruiterRow.company == r["company"],
            RecruiterRow.created_at == created_at,
        )):
            continue
        row = RecruiterRow(
            id=_free_id(db, RecruiterRow, r.get("id", key)),
            name=r["name"],
            company=r["company"],
            email=r.get("email") or "",
            phone=r.get("phone"),
            linkedin=r.get("linkedin"),
            notes=r.get("notes"),
            reputation=r.get("reputation", 0),
            total_placements=r.get("total_placements", 0),
            average_rating=r.get("average_rating", 0.0),
            created_at=created_at,
            updated_at=_date(r.get("updated_at")),
        )
        _add(db, row, deferred)
        added += 1
    return added


def _add(db, row, deferred: list):
    """Insert rows that keep their old id now; rows needing a new id wait
    until the id sequences have been moved past every kept id."""
    if row.id is None:
        deferred.append(row)
    else:
        db.add(row)
        db.flush()


def _reset_id_sequences(db):
    """Postgres: move id sequences past existing ids, or the next insert collides"""
    if db.get_bind().dialect.name != "postgresql":
        return
    for model in (PostRow, RecruiterRow):
        table = model.__tablename__
        max_id = db.scalar(select(func.max(model.id)))
        if max_id:
            db.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), :max_id)"
            ), {"max_id": max_id})


def run_import(db, data_dir: Path) -> dict:
    deferred = []
    counts = {
        "posts": import_posts(db, _load(data_dir / "posts.json"), deferred),
        "users": import_users(db, _load(data_dir / "users.json"), deferred),
        "recruiters": import_recruiters(db, _load(data_dir / "recruiters.json"), deferred),
    }
    _reset_id_sequences(db)
    db.add_all(deferred)
    db.flush()
    db.commit()
    return counts


def main():
    if settings.use_supabase_rest:
        # Keeping old ids needs a direct connection (to move the id sequences),
        # and without this check the import would go to the local SQLite file.
        print(
            "This script needs a direct database connection (DATABASE_URL), but\n"
            "SUPABASE_URL/SUPABASE_KEY are set. Run it from a machine that can reach\n"
            "the database, with only DATABASE_URL set."
        )
        sys.exit(1)
    data_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    with SessionLocal() as db:
        counts = run_import(db, data_dir)
    for name, count in counts.items():
        print(f"{name}: {count} imported")


if __name__ == "__main__":
    main()
