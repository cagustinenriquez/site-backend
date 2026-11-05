import pytest


@pytest.fixture
def add_interviewer(client, auth_headers):
    def _add(name="Dana Lee", company="Initech", **fields):
        response = client.post(
            "/interviewers",
            json={"name": name, "company": company, **fields},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        return response.json()
    return _add


def names(response):
    assert response.status_code == 200, response.text
    return [i["name"] for i in response.json()["interviewers"]]


def test_list_empty(client, auth_headers):
    response = client.get("/interviewers", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"interviewers": [], "total": 0, "page": 1, "limit": 10}


def test_create_saves_all_fields_including_rating(client, auth_headers, add_interviewer):
    created = add_interviewer(
        role="Senior SRE", rating=4.2, interview_types=["take_home", "coding"],
        email="", linkedin="https://linkedin.com/in/dana", notes="kind",
    )
    assert created["id"] == "1"
    assert created["role"] == "Senior SRE"
    assert created["rating"] == 4.2
    assert created["interview_types"] == ["take_home", "coding"]
    assert created["created_at"] and created["updated_at"]

    fetched = client.get(f"/interviewers/{created['id']}", headers=auth_headers).json()
    assert fetched == created


def test_create_defaults(add_interviewer):
    created = add_interviewer()
    assert (created["role"], created["email"], created["linkedin"], created["notes"]) == (None, "", None, None)
    assert created["interview_types"] == []
    assert created["rating"] == 0.0


@pytest.mark.parametrize("fields", [
    {"name": ""},
    {"company": ""},
    {"rating": 5.5},
    {"rating": -1},
    {"interview_types": ["juggling"]},
])
def test_create_validation(client, auth_headers, fields):
    body = {"name": "N", "company": "C", **fields}
    assert client.post("/interviewers", json=body, headers=auth_headers).status_code == 422


def test_get_missing(client, auth_headers):
    for path in ["/interviewers/999", "/interviewers/abc"]:
        response = client.get(path, headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Interviewer not found"


def test_sort(client, auth_headers, add_interviewer):
    add_interviewer("Evan Park", rating=2)
    add_interviewer("Dana Lee", rating=4.5)
    add_interviewer("Fran Diaz", rating=3.5)
    add_interviewer("Ari Cole", rating=4.5)

    # Highest rating first, ties by name
    assert names(client.get("/interviewers", headers=auth_headers)) == [
        "Ari Cole", "Dana Lee", "Fran Diaz", "Evan Park",
    ]
    assert names(client.get("/interviewers", params={"sort": "name"}, headers=auth_headers)) == [
        "Ari Cole", "Dana Lee", "Evan Park", "Fran Diaz",
    ]
    # Newest first
    assert names(client.get("/interviewers", params={"sort": "created_at"}, headers=auth_headers)) == [
        "Ari Cole", "Fran Diaz", "Dana Lee", "Evan Park",
    ]
    assert client.get("/interviewers", params={"sort": "bogus"}, headers=auth_headers).status_code == 422


def test_paging(client, auth_headers, add_interviewer):
    for n in range(5):
        add_interviewer(f"Person {n}", rating=3)
    response = client.get("/interviewers", params={"page": 2, "limit": 2}, headers=auth_headers)
    assert names(response) == ["Person 2", "Person 3"]
    assert response.json()["total"] == 5


def test_search_by_name_company_or_role(client, auth_headers, add_interviewer):
    add_interviewer("Dana Lee", "Initech", role="Staff Engineer")
    add_interviewer("Evan Park", "Globex", role="Eng Manager")
    add_interviewer("Fran Diaz", "Initech")

    def search(term):
        return names(client.get("/interviewers", params={"search": term, "sort": "name"}, headers=auth_headers))

    assert search("manager") == ["Evan Park"]
    assert search("INITECH") == ["Dana Lee", "Fran Diaz"]
    assert search("fran") == ["Fran Diaz"]
    assert search("nobody") == []


def test_type_filter(client, auth_headers, add_interviewer):
    add_interviewer("Dana Lee", interview_types=["system_design"])
    add_interviewer("Evan Park", interview_types=["behavioral"])
    add_interviewer("Fran Diaz", interview_types=["coding", "pair_programming"])
    add_interviewer("Gail Kim", "Hooli", interview_types=["coding"])

    def by_type(**params):
        return names(client.get("/interviewers", params={"sort": "name", **params}, headers=auth_headers))

    assert by_type(type="coding") == ["Fran Diaz", "Gail Kim"]
    assert by_type(type="pair_programming") == ["Fran Diaz"]
    assert by_type(type="take_home") == []
    # Combines with search
    assert by_type(type="coding", search="hooli") == ["Gail Kim"]
    response = client.get("/interviewers", params={"type": "coding"}, headers=auth_headers)
    assert response.json()["total"] == 2
    assert client.get("/interviewers", params={"type": "juggling"}, headers=auth_headers).status_code == 422


def test_update(client, auth_headers, add_interviewer):
    created = add_interviewer(role="Eng Manager", rating=2, interview_types=["behavioral"])
    response = client.put(
        f"/interviewers/{created['id']}",
        json={"rating": 3, "interview_types": ["behavioral", "other"]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 3
    assert data["interview_types"] == ["behavioral", "other"]
    # Fields not sent are kept
    assert (data["name"], data["role"]) == ("Dana Lee", "Eng Manager")
    assert data["updated_at"] >= created["updated_at"]

    assert client.put(f"/interviewers/{created['id']}", json={"rating": 6}, headers=auth_headers).status_code == 422
    missing = client.put("/interviewers/999", json={"rating": 1}, headers=auth_headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Interviewer not found"


def test_delete_does_not_reuse_ids(client, auth_headers, add_interviewer):
    add_interviewer("A")
    second = add_interviewer("B")
    assert client.delete(f"/interviewers/{second['id']}", headers=auth_headers).status_code == 200
    assert client.get(f"/interviewers/{second['id']}", headers=auth_headers).status_code == 404
    assert add_interviewer("C")["id"] == "3"
    missing = client.delete("/interviewers/999", headers=auth_headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Interviewer not found"


@pytest.mark.parametrize("method,url,body", [
    ("get", "/interviewers", None),
    ("get", "/interviewers/1", None),
    ("post", "/interviewers", {"name": "N", "company": "C"}),
    ("put", "/interviewers/1", {"name": "N"}),
    ("delete", "/interviewers/1", None),
    ("get", "/interviewers/1/comments", None),
    ("post", "/interviewers/1/comments", {"body": "hi"}),
    ("delete", "/interviewers/1/comments/1", None),
])
def test_requires_token(client, method, url, body):
    assert client.request(method, url, json=body).status_code == 403


# Comments


@pytest.fixture
def add_comment(client, auth_headers):
    def _add(interviewer_id, body="Gave great hints"):
        response = client.post(
            f"/interviewers/{interviewer_id}/comments", json={"body": body}, headers=auth_headers
        )
        assert response.status_code == 200, response.text
        return response.json()
    return _add


def test_comment_create_and_list(client, auth_headers, add_interviewer, add_comment):
    interviewer = add_interviewer()
    url = f"/interviewers/{interviewer['id']}/comments"
    assert client.get(url, headers=auth_headers).json() == []

    first = add_comment(interviewer["id"], "  gave great hints \n")
    assert first["id"] == "1"
    assert first["interviewer_id"] == interviewer["id"]
    assert first["author"] == "admin"
    assert first["body"] == "gave great hints"

    second = add_comment(interviewer["id"], "followed up with feedback")
    assert [c["id"] for c in client.get(url, headers=auth_headers).json()] == [second["id"], first["id"]]


def test_comment_author_is_logged_in_user(client, db):
    from app.users import create_user

    create_user(db, "maria", "maria-password-123")
    token = client.post(
        "/auth/login", json={"username": "maria", "password": "maria-password-123"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    interviewer = client.post(
        "/interviewers", json={"name": "Dana", "company": "Initech"}, headers=headers
    ).json()

    response = client.post(
        f"/interviewers/{interviewer['id']}/comments",
        json={"body": "hi", "author": "someone-else"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["author"] == "maria"


def test_comments_are_per_interviewer(client, auth_headers, add_interviewer, add_comment):
    a, b = add_interviewer("A"), add_interviewer("B")
    add_comment(a["id"], "about A")
    assert client.get(f"/interviewers/{b['id']}/comments", headers=auth_headers).json() == []


@pytest.mark.parametrize("body", ["", "   \n\t ", "x" * 2001])
def test_comment_body_validation(client, auth_headers, add_interviewer, body):
    interviewer = add_interviewer()
    response = client.post(
        f"/interviewers/{interviewer['id']}/comments", json={"body": body}, headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("interviewer_id", ["999", "abc"])
def test_comments_on_missing_interviewer(client, auth_headers, method, interviewer_id):
    kwargs = {"json": {"body": "hi"}} if method == "post" else {}
    response = getattr(client, method)(
        f"/interviewers/{interviewer_id}/comments", headers=auth_headers, **kwargs
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Interviewer not found"


def test_comment_delete(client, auth_headers, add_interviewer, add_comment):
    a, b = add_interviewer("A"), add_interviewer("B")
    keep = add_comment(a["id"], "keep")
    gone = add_comment(a["id"], "gone")
    url = f"/interviewers/{a['id']}/comments"

    # Must belong to the interviewer in the path
    wrong = client.delete(f"/interviewers/{b['id']}/comments/{gone['id']}", headers=auth_headers)
    assert wrong.status_code == 404
    assert wrong.json()["detail"] == "Comment not found"

    assert client.delete(f"{url}/{gone['id']}", headers=auth_headers).status_code == 200
    assert [c["id"] for c in client.get(url, headers=auth_headers).json()] == [keep["id"]]

    again = client.delete(f"{url}/{gone['id']}", headers=auth_headers)
    assert again.status_code == 404
    assert again.json()["detail"] == "Comment not found"


def test_deleting_interviewer_deletes_its_comments(client, auth_headers, sql_db, add_interviewer, add_comment):
    from sqlalchemy import select

    from app.db_models import InterviewerCommentRow

    a, b = add_interviewer("A"), add_interviewer("B")
    add_comment(a["id"])
    add_comment(a["id"])
    add_comment(b["id"])

    assert client.delete(f"/interviewers/{a['id']}", headers=auth_headers).status_code == 200
    remaining = sql_db.scalars(select(InterviewerCommentRow.interviewer_id)).all()
    assert remaining == [int(b["id"])]
