from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def get_auth_token():
    """Get JWT token for testing"""
    response = client.post("/auth/login", json={"password": "admin"})
    assert response.status_code == 200
    return response.json()["access_token"]


def get_auth_headers(token: str) -> dict:
    """Get authorization headers with token"""
    return {"Authorization": f"Bearer {token}"}


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


def test_login():
    """Test login endpoint"""
    response = client.post("/auth/login", json={"password": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid():
    """Test login with invalid password"""
    response = client.post("/auth/login", json={"password": "wrong"})
    assert response.status_code == 401


def test_list_posts():
    """Test list posts endpoint"""
    response = client.get("/posts")
    assert response.status_code == 200
    data = response.json()
    assert "posts" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert data["total"] >= 1


def test_get_post():
    """Test get single post endpoint"""
    response = client.get("/posts/welcome-to-my-blog")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "welcome-to-my-blog"
    assert data["title"] == "Welcome to My Blog"


def test_get_post_not_found():
    """Test getting non-existent post"""
    response = client.get("/posts/non-existent")
    assert response.status_code == 404


def test_create_post_unauthorized():
    """Test creating post without authentication"""
    new_post = {
        "title": "Test Post",
        "content": "This is a test post",
        "tags": ["test"]
    }
    response = client.post("/posts", json=new_post)
    assert response.status_code == 403


def test_create_post():
    """Test creating a new post with authentication"""
    token = get_auth_token()
    new_post = {
        "title": "Test Post",
        "content": "This is a test post",
        "tags": ["test"]
    }
    response = client.post(
        "/posts",
        json=new_post,
        headers=get_auth_headers(token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Post"
    assert data["slug"] == "test-post"


def test_update_post_unauthorized():
    """Test updating post without authentication"""
    update_data = {"title": "Updated Title"}
    response = client.put("/posts/welcome-to-my-blog", json=update_data)
    assert response.status_code == 403


def test_update_post():
    """Test updating a post with authentication"""
    token = get_auth_token()
    update_data = {"title": "Updated Title"}
    response = client.put(
        "/posts/welcome-to-my-blog",
        json=update_data,
        headers=get_auth_headers(token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


def test_delete_post_unauthorized():
    """Test deleting post without authentication"""
    response = client.delete("/posts/welcome-to-my-blog")
    assert response.status_code == 403


def test_delete_post():
    """Test deleting a post with authentication"""
    token = get_auth_token()

    # First create a post to delete
    new_post = {
        "title": "Delete Me",
        "content": "This will be deleted",
        "tags": ["delete"]
    }
    create_response = client.post(
        "/posts",
        json=new_post,
        headers=get_auth_headers(token)
    )
    slug = create_response.json()["slug"]

    # Then delete it
    response = client.delete(
        f"/posts/{slug}",
        headers=get_auth_headers(token)
    )
    assert response.status_code == 200

    # Verify it's deleted
    get_response = client.get(f"/posts/{slug}")
    assert get_response.status_code == 404
