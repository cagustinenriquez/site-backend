from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to agustinenriquez.dev API"


def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_posts():
    """Test list posts endpoint"""
    response = client.get("/posts")
    assert response.status_code == 200
    data = response.json()
    assert "posts" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data


def test_get_post():
    """Test get single post endpoint"""
    response = client.get("/posts/first-post")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "first-post"
    assert data["title"] == "Welcome to My Blog"


def test_get_post_not_found():
    """Test getting non-existent post"""
    response = client.get("/posts/non-existent")
    assert response.status_code == 404
