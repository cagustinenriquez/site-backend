"""The Supabase REST client (no server needed)."""
from app.storage import SupabaseRest


def test_legacy_jwt_key_sent_as_apikey_and_bearer():
    client = SupabaseRest("https://example.supabase.co", "eyJhbGciOiJIUzI1NiJ9.e30.sig")
    assert client.http.headers["apikey"] == "eyJhbGciOiJIUzI1NiJ9.e30.sig"
    assert client.http.headers["authorization"] == "Bearer eyJhbGciOiJIUzI1NiJ9.e30.sig"


def test_new_secret_key_sent_only_as_apikey():
    client = SupabaseRest("https://example.supabase.co", "sb_secret_abc123")
    assert client.http.headers["apikey"] == "sb_secret_abc123"
    assert "authorization" not in client.http.headers


def test_rest_api_path():
    client = SupabaseRest("https://example.supabase.co/", "sb_secret_abc123")
    assert str(client.http.base_url) == "https://example.supabase.co/rest/v1/"


def test_requests_go_through_https_proxy(monkeypatch):
    """PythonAnywhere free accounts must reach Supabase via their https_proxy"""
    import socket
    import threading

    import httpx
    import pytest

    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    seen = []

    def fake_proxy():
        conn, _ = server.accept()
        seen.append(conn.recv(1024).split(b"\r\n")[0])
        conn.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
        conn.close()

    thread = threading.Thread(target=fake_proxy, daemon=True)
    thread.start()
    monkeypatch.setenv("https_proxy", f"http://127.0.0.1:{server.getsockname()[1]}")
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("no_proxy", raising=False)
    monkeypatch.delenv("NO_PROXY", raising=False)

    client = SupabaseRest("https://example.supabase.co", "sb_secret_abc123", timeout=5)
    with pytest.raises(httpx.HTTPError):
        client.request("GET", "posts")
    thread.join(5)
    server.close()
    assert seen == [b"CONNECT example.supabase.co:443 HTTP/1.1"]
