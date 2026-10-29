"""
WSGI entry point, for hosts that only run WSGI apps (PythonAnywhere's Web tab).

FastAPI is an ASGI app, so this adapter runs each WSGI request through it on
its own event loop.

PythonAnywhere: in the Web tab's WSGI configuration file, replace everything
with:

    import sys
    sys.path.insert(0, "/home/<your-username>/site-backend")
    from wsgi import application  # noqa

Settings (SECRET_KEY, DATABASE_URL, ...) come from the project's .env file.
"""
import asyncio
import sys
from http import HTTPStatus
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import app  # noqa: E402


def _wsgi_str_to_utf8(value: str) -> str:
    """WSGI passes paths as latin-1 decoded bytes; ASGI wants real text"""
    return value.encode("latin-1").decode("utf-8", errors="replace")


def _headers(environ) -> list:
    headers = []
    if environ.get("CONTENT_TYPE"):
        headers.append((b"content-type", environ["CONTENT_TYPE"].encode("latin-1")))
    if environ.get("CONTENT_LENGTH"):
        headers.append((b"content-length", environ["CONTENT_LENGTH"].encode("latin-1")))
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            name = key[5:].replace("_", "-").lower()
            headers.append((name.encode("latin-1"), value.encode("latin-1")))
    return headers


def _read_body(environ) -> bytes:
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    return environ["wsgi.input"].read(length) if length > 0 else b""


async def _call_app(scope: dict, body: bytes) -> dict:
    """Run one request through the ASGI app; return its status, headers and body"""
    response = {"status": None, "headers": [], "body": []}
    response_done = asyncio.Event()
    request_sent = False

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        # Like a real server: only report a disconnect once the response is out.
        # Reporting it early makes middleware stop sending the response body.
        await response_done.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        if message["type"] == "http.response.start":
            response["status"] = message["status"]
            response["headers"] = message.get("headers", [])
        elif message["type"] == "http.response.body":
            response["body"].append(message.get("body", b""))
            if not message.get("more_body", False):
                response_done.set()

    await app(scope, receive, send)
    if response["status"] is None:
        raise RuntimeError("ASGI app finished without sending a response")
    return response


def application(environ, start_response):
    path = _wsgi_str_to_utf8(environ.get("PATH_INFO") or "/")
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": environ.get("SERVER_PROTOCOL", "HTTP/1.1").split("/")[-1],
        "method": environ.get("REQUEST_METHOD", "GET"),
        "scheme": environ.get("wsgi.url_scheme", "http"),
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": environ.get("QUERY_STRING", "").encode("latin-1"),
        "root_path": _wsgi_str_to_utf8(environ.get("SCRIPT_NAME", "")),
        "headers": _headers(environ),
        "server": (environ.get("SERVER_NAME", "localhost"), int(environ.get("SERVER_PORT") or 80)),
        "client": (environ.get("REMOTE_ADDR", "127.0.0.1"), 0),
    }

    # A fresh event loop per request: simple and safe under any WSGI server.
    # FastAPI's worker threads for sync handlers are cleaned up with the loop.
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(_call_app(scope, _read_body(environ)))
    finally:
        loop.close()

    status = response["status"]
    try:
        reason = HTTPStatus(status).phrase
    except ValueError:
        reason = ""
    headers = [(name.decode("latin-1"), value.decode("latin-1")) for name, value in response["headers"]]
    start_response(f"{status} {reason}".strip(), headers)
    return response["body"]
