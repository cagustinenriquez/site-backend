import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from app.db import Base, normalize_database_url
from app.db_models import PostRow, RecruiterRow, UserRow

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import import_json_data  # noqa: E402


@pytest.mark.parametrize("url,expected", [
    ("postgresql://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
    ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
    ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
    ("sqlite:///./data/app.db", "sqlite:///./data/app.db"),
])
def test_normalize_database_url(url, expected):
    assert normalize_database_url(url) == expected


def test_migrations_match_models(tmp_path):
    """`alembic upgrade head` must produce exactly the tables in app/db_models.py.

    Fails when a model changes without a new migration
    (fix: uv run alembic revision --autogenerate -m "...").
    """
    url = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'migrate.db'}"
    url = normalize_database_url(url)
    engine = create_engine(url)
    if engine.dialect.name == "postgresql":
        # Start empty: the other tests use create_all on this database
        Base.metadata.drop_all(engine)
        with engine.begin() as conn:
            conn.exec_driver_sql("DROP TABLE IF EXISTS alembic_version")

    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(config, "head")

    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []

    command.downgrade(config, "base")
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP TABLE IF EXISTS alembic_version")
    engine.dispose()


@pytest.fixture
def json_dir(tmp_path):
    files = {
        "posts.json": {
            "hello": {"id": "7", "slug": "hello", "title": "Hello", "content": "Hi",
                      "excerpt": "Hi", "tags": ["a"], "date": "2026-09-01T10:00:00"},
        },
        "users.json": {
            "agustin": {"username": "agustin", "hashed_password": "$argon2id$v=19$fake"},
        },
        "recruiters.json": {
            "5": {"id": "5", "name": "Jane", "company": "Acme", "email": "",
                  "reputation": 2, "total_placements": 1, "average_rating": 4.0,
                  "created_at": "2026-10-01T00:00:00", "updated_at": "2026-10-02T00:00:00"},
        },
    }
    for name, data in files.items():
        (tmp_path / name).write_text(json.dumps(data))
    return tmp_path


def _run_import(db, data_dir):
    counts = import_json_data.run_import(db, data_dir)
    return counts["posts"], counts["users"], counts["recruiters"]


def test_import_json_data(db, json_dir):
    assert _run_import(db, json_dir) == (1, 1, 1)

    post = db.query(PostRow).filter_by(slug="hello").one()
    assert (post.id, post.tags) == (7, ["a"])
    assert db.get(UserRow, "agustin").hashed_password == "$argon2id$v=19$fake"
    assert db.get(RecruiterRow, 5).name == "Jane"

    # Running it again adds nothing
    assert _run_import(db, json_dir) == (0, 0, 0)


def test_import_then_create_does_not_collide(db, json_dir):
    """New rows get ids after the imported ones (needs the Postgres sequence reset)"""
    from app.crud import create_post
    from app.models import PostCreate, RecruiterCreate
    from app.recruiters import create_recruiter

    _run_import(db, json_dir)

    assert int(create_post(db, PostCreate(title="New", content="C")).id) > 7
    assert int(create_recruiter(db, RecruiterCreate(name="New", company="Co")).id) > 5


def test_import_when_ids_already_taken(db, json_dir):
    """Rows created before the import keep their ids; imported rows get new ones"""
    from app.models import RecruiterCreate
    from app.recruiters import create_recruiter

    # The seed post already has id 1. Take ids 2..7 for posts and 1..5 for recruiters.
    for n in range(2, 8):
        db.add(PostRow(slug=f"existing-{n}", title="T", content="C", tags=[],
                       date=datetime(2026, 1, 1)))
    db.commit()
    for n in range(5):
        create_recruiter(db, RecruiterCreate(name=f"Existing {n}", company="Co"))

    assert _run_import(db, json_dir) == (1, 1, 1)

    imported_post = db.query(PostRow).filter_by(slug="hello").one()
    assert imported_post.id not in range(1, 8)
    assert db.get(PostRow, 7).slug == "existing-7"

    imported = db.query(RecruiterRow).filter_by(name="Jane").one()
    assert imported.id > 5
    assert db.get(RecruiterRow, 5).name == "Existing 4"

    # Still safe to run again
    assert _run_import(db, json_dir) == (0, 0, 0)
    assert db.query(RecruiterRow).filter_by(name="Jane").count() == 1


def test_import_missing_files_is_noop(db, tmp_path):
    assert _run_import(db, tmp_path) == (0, 0, 0)
