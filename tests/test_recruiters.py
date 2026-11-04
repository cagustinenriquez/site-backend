import pytest


@pytest.fixture
def add_recruiter(client, auth_headers):
    def _add(name="Jane Doe", company="Acme", **fields):
        response = client.post(
            "/recruiters",
            json={"name": name, "company": company, **fields},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        return response.json()
    return _add


def test_list_empty(client, auth_headers):
    response = client.get("/recruiters", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"recruiters": [], "total": 0, "page": 1, "limit": 10}


def test_create_and_get(client, auth_headers, add_recruiter):
    created = add_recruiter(email="", reputation=-2, notes="ghosted me")
    assert created["id"] == "1"
    assert created["reputation"] == -2
    assert created["total_placements"] == 0
    assert created["average_rating"] == 0.0

    fetched = client.get(f"/recruiters/{created['id']}", headers=auth_headers).json()
    assert fetched["notes"] == "ghosted me"


def test_get_missing(client, auth_headers):
    assert client.get("/recruiters/999", headers=auth_headers).status_code == 404


def test_sort_and_search(client, auth_headers, add_recruiter):
    add_recruiter("Low", "Acme", reputation=-1)
    add_recruiter("High", "Globex", reputation=5)
    add_recruiter("Mid", "Acme", reputation=2)

    listing = client.get("/recruiters", headers=auth_headers).json()
    names = [r["name"] for r in listing["recruiters"]]
    assert names == ["High", "Mid", "Low"]

    acme = client.get("/recruiters", params={"search": "acme"}, headers=auth_headers).json()
    assert acme["total"] == 2

    bogus = client.get("/recruiters", params={"sort": "bogus"}, headers=auth_headers)
    assert bogus.status_code == 422


def test_update(client, auth_headers, add_recruiter):
    created = add_recruiter()
    response = client.put(
        f"/recruiters/{created['id']}",
        json={"reputation": 3, "total_placements": 2, "average_rating": 4.5},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert (data["reputation"], data["total_placements"], data["average_rating"]) == (3, 2, 4.5)
    assert data["name"] == "Jane Doe"


def test_delete_does_not_reuse_ids(client, auth_headers, add_recruiter):
    add_recruiter("A")
    second = add_recruiter("B")
    assert client.delete(f"/recruiters/{second['id']}", headers=auth_headers).status_code == 200
    # Deleted ids are never handed out again, even the highest one
    assert add_recruiter("C")["id"] == "3"
    first_gone = client.delete("/recruiters/1", headers=auth_headers)
    assert first_gone.status_code == 200
    assert add_recruiter("D")["id"] == "4"


@pytest.mark.parametrize("method,url,body", [
    ("get", "/recruiters", None),
    ("get", "/recruiters/1", None),
    ("post", "/recruiters", {"name": "N", "company": "C"}),
    ("put", "/recruiters/1", {"name": "N"}),
    ("delete", "/recruiters/1", None),
])
def test_requires_token(client, method, url, body):
    assert client.request(method, url, json=body).status_code == 403


# Comments


@pytest.fixture
def add_comment(client, auth_headers):
    def _add(recruiter_id, body="Responsive and honest"):
        response = client.post(
            f"/recruiters/{recruiter_id}/comments", json={"body": body}, headers=auth_headers
        )
        assert response.status_code == 200, response.text
        return response.json()
    return _add


def test_comment_create_and_list(client, auth_headers, add_recruiter, add_comment):
    recruiter = add_recruiter()
    assert client.get(f"/recruiters/{recruiter['id']}/comments", headers=auth_headers).json() == []

    first = add_comment(recruiter["id"], "  first call went well \n")
    assert first["id"] == "1"
    assert first["recruiter_id"] == recruiter["id"]
    assert first["author"] == "admin"
    assert first["body"] == "first call went well"
    assert first["created_at"]

    second = add_comment(recruiter["id"], "then ghosted")
    comments = client.get(f"/recruiters/{recruiter['id']}/comments", headers=auth_headers).json()
    assert [c["id"] for c in comments] == [second["id"], first["id"]]


def test_comment_author_is_logged_in_user(client, db):
    from app.users import create_user

    create_user(db, "maria", "maria-password-123")
    token = client.post(
        "/auth/login", json={"username": "maria", "password": "maria-password-123"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    recruiter = client.post(
        "/recruiters", json={"name": "Jane", "company": "Acme"}, headers=headers
    ).json()

    response = client.post(
        f"/recruiters/{recruiter['id']}/comments",
        # A client-sent author is ignored
        json={"body": "hi", "author": "someone-else"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["author"] == "maria"


def test_comments_are_per_recruiter(client, auth_headers, add_recruiter, add_comment):
    a, b = add_recruiter("A", "Acme"), add_recruiter("B", "Globex")
    add_comment(a["id"], "about A")
    comments = client.get(f"/recruiters/{b['id']}/comments", headers=auth_headers).json()
    assert comments == []


@pytest.mark.parametrize("body", ["", "   \n\t ", "x" * 2001])
def test_comment_body_validation(client, auth_headers, add_recruiter, body):
    recruiter = add_recruiter()
    response = client.post(
        f"/recruiters/{recruiter['id']}/comments", json={"body": body}, headers=auth_headers
    )
    assert response.status_code == 422


def test_comment_body_max_length(add_recruiter, add_comment):
    # The limit applies after trimming
    comment = add_comment(add_recruiter()["id"], " " + "x" * 2000 + " ")
    assert len(comment["body"]) == 2000


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("recruiter_id", ["999", "abc"])
def test_comments_on_missing_recruiter(client, auth_headers, method, recruiter_id):
    kwargs = {"json": {"body": "hi"}} if method == "post" else {}
    response = getattr(client, method)(
        f"/recruiters/{recruiter_id}/comments", headers=auth_headers, **kwargs
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Recruiter not found"


def test_comment_delete(client, auth_headers, add_recruiter, add_comment):
    recruiter = add_recruiter()
    keep = add_comment(recruiter["id"], "keep")
    gone = add_comment(recruiter["id"], "gone")

    url = f"/recruiters/{recruiter['id']}/comments"
    response = client.delete(f"{url}/{gone['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert [c["id"] for c in client.get(url, headers=auth_headers).json()] == [keep["id"]]

    again = client.delete(f"{url}/{gone['id']}", headers=auth_headers)
    assert again.status_code == 404
    assert again.json()["detail"] == "Comment not found"


def test_comment_delete_needs_matching_recruiter(client, auth_headers, add_recruiter, add_comment):
    a, b = add_recruiter("A", "Acme"), add_recruiter("B", "Globex")
    comment = add_comment(a["id"])
    for path in [f"/recruiters/{b['id']}/comments/{comment['id']}", "/recruiters/1/comments/abc"]:
        response = client.delete(path, headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Comment not found"
    assert len(client.get(f"/recruiters/{a['id']}/comments", headers=auth_headers).json()) == 1


def test_deleting_recruiter_deletes_its_comments(client, auth_headers, sql_db, add_recruiter, add_comment):
    from sqlalchemy import func, select

    from app.db_models import RecruiterCommentRow

    a, b = add_recruiter("A", "Acme"), add_recruiter("B", "Globex")
    add_comment(a["id"])
    add_comment(a["id"])
    add_comment(b["id"])

    assert client.delete(f"/recruiters/{a['id']}", headers=auth_headers).status_code == 200
    remaining = sql_db.scalars(select(RecruiterCommentRow.recruiter_id)).all()
    assert remaining == [int(b["id"])]
    assert sql_db.scalar(select(func.count()).select_from(RecruiterCommentRow)) == 1


@pytest.mark.parametrize("method, path", [
    ("get", "/recruiters/1/comments"),
    ("post", "/recruiters/1/comments"),
    ("delete", "/recruiters/1/comments/1"),
])
def test_comments_require_auth(client, add_recruiter, method, path):
    add_recruiter()
    response = getattr(client, method)(path)
    assert response.status_code in (401, 403)
