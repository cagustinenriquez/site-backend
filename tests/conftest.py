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

import time  # noqa: E402
from datetime import datetime  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from jose import jwt  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import db_models  # noqa: E402
from app.db import Base, create_db_engine, get_db  # noqa: E402
from app.limiter import limiter  # noqa: E402
from app.storage import SupabaseError, SupabaseRest  # noqa: E402
from main import app  # noqa: E402

# Which backend the suite runs against:
# - default: in-memory SQLite through SQLAlchemy
# - TEST_DATABASE_URL: a real Postgres through SQLAlchemy, e.g.
#     TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:55432/test
# - TEST_POSTGREST_URL (+ TEST_DATABASE_URL for setup): the Supabase REST
#   backend against a local PostgREST, see docker-compose.test.yml / make test-rest
# These databases are wiped for every test, so never point them at real data.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
TEST_POSTGREST_URL = os.environ.get("TEST_POSTGREST_URL")
TEST_POSTGREST_JWT_SECRET = os.environ.get(
    "TEST_POSTGREST_JWT_SECRET", "test-jwt-secret-at-least-32-characters-long"
)
REST_MODE = bool(TEST_POSTGREST_URL)
if REST_MODE and not TEST_DATABASE_URL:
    raise RuntimeError("TEST_POSTGREST_URL also needs TEST_DATABASE_URL (to create the tables)")

TABLES = ["posts", "recruiters", "users"]


def postgrest_key(role: str) -> str:
    """An API key for the local PostgREST, like Supabase's anon/service_role keys"""
    return jwt.encode({"role": role}, TEST_POSTGREST_JWT_SECRET, algorithm="HS256")


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
    if engine.dialect.name == "postgresql":
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def _wait_for_postgrest(client):
    """PostgREST reloads its schema cache asynchronously after NOTIFY"""
    for _ in range(50):
        try:
            client.request("GET", "posts", params={"limit": 1})
            return
        except SupabaseError:
            time.sleep(0.2)
    raise RuntimeError("PostgREST never picked up the test tables")


@pytest.fixture(scope="session")
def rest_client(engine):
    """REST mode: the Supabase REST client, using a service_role key"""
    if not REST_MODE:
        yield None
        return
    with engine.begin() as conn:
        # Like the real migration on Supabase: RLS on, no policies
        for name in TABLES:
            conn.exec_driver_sql(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
        conn.exec_driver_sql("NOTIFY pgrst, 'reload schema'")
    client = SupabaseRest(TEST_POSTGREST_URL, postgrest_key("service_role"), rest_path="")
    _wait_for_postgrest(client)
    yield client
    client.close()


@pytest.fixture(autouse=True)
def session_factory(engine, rest_client):
    """Empty tables with one seed post for every test"""
    if engine.dialect.name == "postgresql":
        # Tables live for the whole session (PostgREST caches them); a test
        # may have dropped them (migration test), so recreate if missing.
        Base.metadata.create_all(engine)
        with engine.begin() as conn:
            conn.exec_driver_sql(
                "TRUNCATE " + ", ".join(f'"{t}"' for t in TABLES) + " RESTART IDENTITY CASCADE"
            )
    else:
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
        if REST_MODE:
            yield rest_client
            return
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    yield factory
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def db(session_factory, rest_client):
    """The backend under test (SQL session or REST client), for direct store calls"""
    if REST_MODE:
        yield rest_client
        return
    with session_factory() as session:
        yield session


@pytest.fixture
def sql_db(session_factory):
    """A SQLAlchemy session on the test database, whatever the backend"""
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
