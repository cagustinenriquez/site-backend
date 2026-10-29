def test_login_rate_limited(client, admin_password):
    """Login allows 5 attempts per minute, then returns 429"""
    for _ in range(5):
        assert client.post("/auth/login", json={"password": "wrong"}).status_code == 401
    response = client.post("/auth/login", json={"password": admin_password})
    assert response.status_code == 429


def test_default_rate_limit(client):
    """Other routes allow 100 requests per minute, then return 429"""
    for _ in range(100):
        assert client.get("/").status_code == 200
    assert client.get("/").status_code == 429


def test_health_not_rate_limited(client):
    """Health checks are exempt from rate limiting"""
    for _ in range(110):
        assert client.get("/health").status_code == 200
