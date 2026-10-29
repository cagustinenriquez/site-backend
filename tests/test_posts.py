# --- Reading ---

def test_list_posts(client):
    response = client.get("/posts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["posts"][0]["slug"] == "welcome-to-my-blog"


def test_list_posts_pagination(client, create_post):
    for title in ["First", "Second", "Third"]:
        create_post(title=title)

    page1 = client.get("/posts", params={"page": 1, "limit": 2}).json()
    page2 = client.get("/posts", params={"page": 2, "limit": 2}).json()
    page3 = client.get("/posts", params={"page": 3, "limit": 2}).json()

    assert page1["total"] == 4
    # Newest first
    assert [p["title"] for p in page1["posts"]] == ["Third", "Second"]
    assert [p["title"] for p in page2["posts"]] == ["First", "Welcome to My Blog"]
    assert page3["posts"] == []


def test_list_posts_invalid_params(client):
    assert client.get("/posts", params={"page": 0}).status_code == 422
    assert client.get("/posts", params={"limit": 0}).status_code == 422
    assert client.get("/posts", params={"limit": 101}).status_code == 422


def test_list_posts_filter_by_tag(client, create_post):
    create_post(title="Python Tips", tags=["python"])

    data = client.get("/posts", params={"tag": "python"}).json()
    assert data["total"] == 1
    assert data["posts"][0]["title"] == "Python Tips"

    assert client.get("/posts", params={"tag": "missing"}).json()["total"] == 0


def test_get_post(client):
    response = client.get("/posts/welcome-to-my-blog")
    assert response.status_code == 200
    assert response.json()["title"] == "Welcome to My Blog"


def test_get_post_not_found(client):
    assert client.get("/posts/non-existent").status_code == 404


# --- Creating ---

def test_create_post(client, create_post):
    post = create_post(title="Test Post", content="Body", tags=["test"])

    assert post["slug"] == "test-post"
    assert post["title"] == "Test Post"
    assert post["tags"] == ["test"]
    assert post["date"]
    # Saved, not just returned
    assert client.get("/posts/test-post").json() == post


def test_create_post_default_excerpt(create_post):
    post = create_post(content="x" * 150)
    assert post["excerpt"] == "x" * 100


def test_create_post_keeps_excerpt(create_post):
    post = create_post(excerpt="Custom excerpt")
    assert post["excerpt"] == "Custom excerpt"


def test_create_post_duplicate_title_gets_unique_slug(create_post):
    slugs = [create_post(title="Same Title")["slug"] for _ in range(3)]
    assert slugs == ["same-title", "same-title-1", "same-title-2"]


def test_create_post_ids_unique_after_delete(client, auth_headers, create_post):
    a = create_post(title="A")
    b = create_post(title="B")
    client.delete(f"/posts/{a['slug']}", headers=auth_headers)
    c = create_post(title="C")

    assert c["id"] != b["id"]


def test_create_post_missing_fields(client, auth_headers):
    response = client.post("/posts", json={"title": "No content"}, headers=auth_headers)
    assert response.status_code == 422


# --- Updating ---

def test_update_post(client, auth_headers):
    response = client.put(
        "/posts/welcome-to-my-blog",
        json={"title": "Updated Title"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    # Fields not sent are unchanged
    assert data["content"] == "This is the first blog post."
    assert data["tags"] == ["welcome", "intro"]
    # Saved, not just returned
    assert client.get("/posts/welcome-to-my-blog").json()["title"] == "Updated Title"


def test_update_post_not_found(client, auth_headers):
    response = client.put("/posts/nope", json={"title": "X"}, headers=auth_headers)
    assert response.status_code == 404


# --- Deleting ---

def test_delete_post(client, auth_headers):
    response = client.delete("/posts/welcome-to-my-blog", headers=auth_headers)
    assert response.status_code == 200
    assert client.get("/posts/welcome-to-my-blog").status_code == 404


def test_delete_post_not_found(client, auth_headers):
    assert client.delete("/posts/nope", headers=auth_headers).status_code == 404
