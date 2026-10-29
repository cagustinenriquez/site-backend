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
