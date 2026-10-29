"""The WSGI adapter used on PythonAnywhere's Web tab."""
import io
import json
import threading

import pytest

from tests.conftest import ADMIN_PASSWORD
from wsgi import application


def call(method="GET", path="/", body=None, headers=None, query=""):
    raw = json.dumps(body).encode() if body is not None else b""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "SERVER_NAME": "testserver",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "10.0.0.1",
        "wsgi.url_scheme": "https",
        "wsgi.input": io.BytesIO(raw),
    }
    if raw:
        environ["CONTENT_TYPE"] = "application/json"
        environ["CONTENT_LENGTH"] = str(len(raw))
    for name, value in (headers or {}).items():
        environ["HTTP_" + name.upper().replace("-", "_")] = value

    captured = {}

    def start_response(status, response_headers):
        captured["status"] = status
        captured["headers"] = dict(response_headers)

    body_bytes = b"".join(application(environ, start_response))
    return captured["status"], captured["headers"], body_bytes


def test_get():
    status, headers, body = call(path="/health")
    assert status == "200 OK"
    assert headers["content-type"] == "application/json"
    assert json.loads(body) == {"status": "ok"}


def test_status_line_uses_real_reason_phrase():
    status, _, _ = call(path="/posts/does-not-exist")
    assert status == "404 Not Found"


def test_query_string():
    _, _, body = call(path="/posts", query="limit=1&page=1")
    assert json.loads(body)["limit"] == 1


def test_post_with_json_body_and_auth_header():
    status, _, body = call("POST", "/auth/login", {"password": ADMIN_PASSWORD})
    assert status == "200 OK"
    token = json.loads(body)["access_token"]

    status, _, body = call(
        "POST", "/posts", {"title": "Vía WSGI", "content": "c"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status == "200 OK"
    assert json.loads(body)["slug"] == "via-wsgi"


@pytest.mark.parametrize("path", ["/posts/por-qué", "/posts/por-qu%C3%A9"])
def test_non_ascii_path_does_not_crash(path):
    # WSGI servers pass PATH_INFO as latin-1 decoded bytes
    wsgi_path = path.encode("utf-8").decode("latin-1")
    status, _, _ = call(path=wsgi_path)
    assert status == "404 Not Found"


def test_threads_do_not_pile_up():
    """Sync handlers run in a thread pool; it must be reused across requests"""
    call(path="/posts")
    before = threading.active_count()
    for _ in range(50):
        call(path="/posts")
    assert threading.active_count() <= before + 2
