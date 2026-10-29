def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to agustinenriquez.dev API"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
