from datetime import timedelta

import pytest
from jose import jwt

from app.auth import ALGORITHM, create_access_token


def test_login(client, admin_password):
    response = client.post("/auth/login", json={"password": admin_password})
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    response = client.post("/auth/login", json={"password": "wrong"})
    assert response.status_code == 401


def test_login_missing_password(client):
    response = client.post("/auth/login", json={})
    assert response.status_code == 422


WRITE_REQUESTS = [
    ("post", "/posts", {"title": "T", "content": "C"}),
    ("put", "/posts/welcome-to-my-blog", {"title": "T"}),
    ("delete", "/posts/welcome-to-my-blog", None),
]


@pytest.mark.parametrize("method,url,body", WRITE_REQUESTS)
def test_write_requires_token(client, method, url, body):
    response = client.request(method, url, json=body)
    assert response.status_code == 403


@pytest.mark.parametrize("method,url,body", WRITE_REQUESTS)
def test_write_rejects_invalid_token(client, method, url, body):
    headers = {"Authorization": "Bearer not-a-real-token"}
    response = client.request(method, url, json=body, headers=headers)
    assert response.status_code == 401


def test_expired_token_rejected(client):
    token = create_access_token({"sub": "admin"}, expires_delta=timedelta(minutes=-1))
    response = client.delete(
        "/posts/welcome-to-my-blog", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_token_signed_with_other_key_rejected(client):
    token = jwt.encode({"sub": "admin"}, "some-other-key", algorithm=ALGORITHM)
    response = client.delete(
        "/posts/welcome-to-my-blog", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
