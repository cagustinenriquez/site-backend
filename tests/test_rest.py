"""Supabase REST backend against a local PostgREST (make test-rest)."""
from datetime import datetime

import pytest

from app.db_models import PostRow
from app.storage import RestTable, SupabaseError, SupabaseRest
from app.users import create_user
from tests.conftest import REST_MODE, TEST_POSTGREST_URL, postgrest_key

needs_postgrest = pytest.mark.skipif(not REST_MODE, reason="needs TEST_POSTGREST_URL (make test-rest)")


@pytest.fixture
def anon():
    """What anyone holding the project's public anon key can do"""
    client = SupabaseRest(TEST_POSTGREST_URL, postgrest_key("anon"), rest_path="")
    yield client
    client.close()


@needs_postgrest
def test_anon_key_cannot_read_tables(db, anon):
    create_user(db, "agustin", "s3cret")
    # Rows exist (the service key sees them) but RLS hides them from anon
    assert db.request("GET", "users").json() != []
    assert anon.request("GET", "users").json() == []
    assert anon.request("GET", "posts").json() == []


@needs_postgrest
def test_anon_key_cannot_write(anon):
    with pytest.raises(SupabaseError):
        anon.request("POST", "posts", json={
            "slug": "x", "title": "x", "content": "x", "tags": [], "date": "2026-01-01T00:00:00",
        })


@needs_postgrest
def test_all_pages_past_row_limit(db, create_post, monkeypatch):
    monkeypatch.setattr(SupabaseRest, "PAGE_SIZE", 2)
    for n in range(4):
        create_post(title=f"Post {n}")
    assert len(RestTable(db, PostRow).all()) == 5  # 4 + the seed post


@needs_postgrest
def test_datetimes_come_back_as_datetimes(db):
    row = RestTable(db, PostRow).get(slug="welcome-to-my-blog")
    assert row["date"] == datetime(2026, 8, 28)


@pytest.mark.parametrize("value", [
    "2026-10-29T12:29:33.79421",   # PostgREST trims trailing zeros
    "2026-10-29T12:29:33.5",
    "2026-10-29T12:29:33",
])
def test_parses_postgrest_datetimes(value):
    from app.storage import _parse_datetime
    assert _parse_datetime(value).year == 2026
