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


def test_login_returns_refresh_token(client, admin_password):
    data = client.post(
        "/auth/login", json={"username": "admin", "password": admin_password}
    ).json()
    assert data["refresh_token"]


def test_fallback_login_requires_admin_username(client, admin_password):
    response = client.post(
        "/auth/login", json={"username": "someone", "password": admin_password}
    )
    assert response.status_code == 401


def test_refresh_returns_working_access_token(client, admin_password):
    tokens = client.post("/auth/login", json={"password": admin_password}).json()
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    new_access = response.json()["access_token"]
    create = client.post(
        "/posts",
        json={"title": "After refresh", "content": "C"},
        headers={"Authorization": f"Bearer {new_access}"},
    )
    assert create.status_code == 200


def test_access_token_cannot_be_used_to_refresh(client, admin_password):
    tokens = client.post("/auth/login", json={"password": admin_password}).json()
    response = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401


def test_refresh_token_cannot_be_used_for_writes(client, admin_password):
    tokens = client.post("/auth/login", json={"password": admin_password}).json()
    response = client.post(
        "/posts",
        json={"title": "T", "content": "C"},
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert response.status_code == 401


def test_users_file_replaces_admin_password(client, admin_password):
    from app.users import create_user

    create_user("agustin", "s3cret")
    ok = client.post("/auth/login", json={"username": "agustin", "password": "s3cret"})
    assert ok.status_code == 200
    # ADMIN_PASSWORD stops working once real users exist
    old = client.post("/auth/login", json={"username": "admin", "password": admin_password})
    assert old.status_code == 401


def _remove_user(username):
    from app import users

    data = users._load_users()
    del data[username]
    users._save_users(data)


def test_fallback_admin_tokens_stop_working_once_users_exist(client, admin_password):
    from app.users import create_user

    tokens = client.post("/auth/login", json={"password": admin_password}).json()
    create_user("agustin", "s3cret")

    refresh = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 401
    write = client.delete(
        "/posts/welcome-to-my-blog",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert write.status_code == 401


def test_tokens_for_removed_user_stop_working(client):
    from app.users import create_user

    create_user("agustin", "s3cret")
    create_user("other", "pw")
    tokens = client.post(
        "/auth/login", json={"username": "agustin", "password": "s3cret"}
    ).json()
    _remove_user("agustin")

    refresh = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 401
    write = client.delete(
        "/posts/welcome-to-my-blog",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert write.status_code == 401
