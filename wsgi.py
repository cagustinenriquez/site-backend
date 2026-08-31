"""
WSGI entry point for PythonAnywhere deployment.
"""
import os
import sys
import asyncio
from io import BytesIO

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Import and expose the FastAPI app
from main import app


class ASGItoWSGI:
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    def __call__(self, environ, start_response):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._run_asgi(environ, start_response))
        finally:
            loop.close()

    async def _run_asgi(self, environ, start_response):
        scope = {
            'type': 'http',
            'asgi': {'version': '3.0'},
            'http_version': '1.1',
            'method': environ.get('REQUEST_METHOD', 'GET'),
            'scheme': environ.get('wsgi.url_scheme', 'http'),
            'path': environ.get('PATH_INFO', '/'),
            'query_string': environ.get('QUERY_STRING', '').encode() if environ.get('QUERY_STRING') else b'',
            'root_path': environ.get('SCRIPT_NAME', ''),
            'headers': self._get_headers(environ),
            'server': (environ.get('SERVER_NAME', 'localhost'), int(environ.get('SERVER_PORT', 80))),
            'client': (environ.get('REMOTE_ADDR', '127.0.0.1'), 0),
            'extensions': {},
        }

        body = self._read_body(environ)
        response_data = BytesIO()
        response_started = False
        status_code = None
        response_headers = []

        async def receive():
            return {'type': 'http.request', 'body': body, 'more_body': False}

        async def send(message):
            nonlocal response_started, status_code, response_headers
            if message['type'] == 'http.response.start':
                response_started = True
                status_code = message['status']
                response_headers = message.get('headers', [])
            elif message['type'] == 'http.response.body':
                body_chunk = message.get('body', b'')
                if body_chunk:
                    response_data.write(body_chunk)

        await self.asgi_app(scope, receive, send)

        # Format headers for WSGI
        headers = []
        for name, value in response_headers:
            if isinstance(name, bytes):
                name = name.decode()
            if isinstance(value, bytes):
                value = value.decode()
            headers.append((name, value))

        start_response(f'{status_code} {"OK" if status_code == 200 else "Error"}', headers)
        response_data.seek(0)
        return [response_data.read()]

    @staticmethod
    def _get_headers(environ):
        headers = []
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-')
                headers.append([header_name.encode(), value.encode()])
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH') and value:
                header_name = key.replace('_', '-')
                headers.append([header_name.encode(), value.encode()])
        return headers

    @staticmethod
    def _read_body(environ):
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError, TypeError):
            return b''
        if content_length > 0:
            return environ['wsgi.input'].read(content_length)
        return b''


application = ASGItoWSGI(app)
