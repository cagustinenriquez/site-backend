import os

# Fixed settings for tests. Set before the app is imported so a developer's
# .env (e.g. a real ADMIN_PASSWORD or disabled rate limits) can't change them.
ADMIN_PASSWORD = "test-password"
os.environ.update({
    "ADMIN_PASSWORD": ADMIN_PASSWORD,
    "SECRET_KEY": "test-secret-key",
    "RATE_LIMIT_ENABLED": "true",
    "RATE_LIMIT_DEFAULT": "100/minute",
    "RATE_LIMIT_LOGIN": "5/minute",
})

import json  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import crud  # noqa: E402
from app.limiter import limiter  # noqa: E402
from main import app  # noqa: E402

SEED_POSTS = {
    "welcome-to-my-blog": {
        "id": "1",
        "slug": "welcome-to-my-blog",
        "title": "Welcome to My Blog",
        "content": "This is the first blog post.",
        "excerpt": "Welcome to the blog",
        "tags": ["welcome", "intro"],
        "date": "2026-08-28T00:00:00",
    }
}


@pytest.fixture(autouse=True)
def posts_file(tmp_path, monkeypatch):
    """Point the app at a fresh posts file per test, never data/posts.json"""
    path = tmp_path / "posts.json"
    path.write_text(json.dumps(SEED_POSTS))
    monkeypatch.setattr(crud, "DATA_DIR", tmp_path)
    monkeypatch.setattr(crud, "POSTS_FILE", path)
    return path


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
