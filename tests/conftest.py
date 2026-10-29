import os

# Fixed settings for tests. Set before the app is imported so a developer's
# .env (e.g. a real ADMIN_PASSWORD, disabled rate limits or a Supabase
# DATABASE_URL) can't change them or be written to.
ADMIN_PASSWORD = "test-password"
os.environ.update({
    "ADMIN_PASSWORD": ADMIN_PASSWORD,
    "SECRET_KEY": "test-secret-key",
    "DATABASE_URL": "sqlite://",
    "RATE_LIMIT_ENABLED": "true",
    "RATE_LIMIT_DEFAULT": "100/minute",
    "RATE_LIMIT_LOGIN": "5/minute",
})

from datetime import datetime  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import db_models  # noqa: E402
from app.db import Base, create_db_engine, get_db  # noqa: E402
from app.limiter import limiter  # noqa: E402
from main import app  # noqa: E402

# Optional: run the suite against a real Postgres, e.g.
#   TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test uv run pytest
# Its tables are dropped and recreated for every test, so never point it at real data.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


def _make_engine():
    if TEST_DATABASE_URL:
        return create_db_engine(TEST_DATABASE_URL)
    # One shared in-memory SQLite connection, usable from FastAPI's threadpool
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
def engine():
    engine = _make_engine()
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def session_factory(engine):
    """Fresh tables with one seed post for every test"""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with factory() as db:
        db.add(db_models.PostRow(
            slug="welcome-to-my-blog",
            title="Welcome to My Blog",
            content="This is the first blog post.",
            excerpt="Welcome to the blog",
            tags=["welcome", "intro"],
            date=datetime(2026, 8, 28),
        ))
        db.commit()

    def override_get_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    yield factory
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)


@pytest.fixture
def db(session_factory):
    """A session on the test database, for setting up data directly"""
    with session_factory() as session:
        yield session


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Start every test with empty rate-limit counters"""
    limiter.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_password():
    return ADMIN_PASSWORD


@pytest.fixture
def auth_headers(client):
    response = client.post("/auth/login", json={"password": ADMIN_PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def create_post(client, auth_headers):
    """Create a post through the API and return its JSON"""
    def _create(title="Test Post", content="This is a test post", **fields):
        response = client.post(
            "/posts",
            json={"title": title, "content": content, **fields},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        return response.json()
    return _create
