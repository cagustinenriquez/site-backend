"""
WSGI entry point for PythonAnywhere deployment.
"""
import os
import sys
import asyncio
from io import BytesIO

# Add the actual project directory to path
sys.path.insert(0, '/home/agustinenriquez/site-backend')

# Import FastAPI app
from main import app


def application(environ, start_response):
    """WSGI application that wraps the FastAPI ASGI app."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Read request body
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError, TypeError):
            content_length = 0

        body = b''
        if content_length > 0:
            body = environ['wsgi.input'].read(content_length)

        # Build ASGI scope with proper headers
        scope = {
            'type': 'http',
            'asgi': {'version': '3.0'},
            'http_version': '1.1',
            'method': environ.get('REQUEST_METHOD', 'GET'),
            'scheme': environ.get('wsgi.url_scheme', 'http'),
            'path': environ.get('PATH_INFO', '/'),
            'query_string': environ.get('QUERY_STRING', '').encode(),
            'root_path': environ.get('SCRIPT_NAME', ''),
            'headers': get_headers(environ),
            'server': (environ.get('SERVER_NAME', 'localhost'), int(environ.get('SERVER_PORT', 80))),
            'client': (environ.get('REMOTE_ADDR', '127.0.0.1'), 0),
        }

        return loop.run_until_complete(run_asgi(app, scope, body, start_response))
    finally:
        loop.close()


async def run_asgi(app, scope, body, start_response):
    """Run the ASGI application and return WSGI response."""
    response_started = False
    response_chunks = []

    async def receive():
        return {'type': 'http.request', 'body': body, 'more_body': False}

    async def send(message):
        nonlocal response_started
        if message['type'] == 'http.response.start':
            response_started = True
            status = message['status']
            headers = []
            for name, value in message.get('headers', []):
                if isinstance(name, bytes):
                    name = name.decode('latin1')
                if isinstance(value, bytes):
                    value = value.decode('latin1')
                headers.append((name, value))
            start_response(f'{status} OK', headers)
        elif message['type'] == 'http.response.body':
            chunk = message.get('body', b'')
            if chunk:
                response_chunks.append(chunk)

    await app(scope, receive, send)
    return response_chunks


def get_headers(environ):
    """Extract HTTP headers from WSGI environ for ASGI."""
    headers = []

    # Add Content-Type if present
    if 'CONTENT_TYPE' in environ:
        headers.append((b'content-type', environ['CONTENT_TYPE'].encode('latin1')))

    # Add Content-Length if present
    if 'CONTENT_LENGTH' in environ and environ['CONTENT_LENGTH']:
        headers.append((b'content-length', environ['CONTENT_LENGTH'].encode('latin1')))

    # Add HTTP headers
    for key, value in environ.items():
        if key.startswith('HTTP_'):
            header_name = key[5:].replace('_', '-').lower()
            headers.append((header_name.encode('latin1'), value.encode('latin1')))

    return headers
