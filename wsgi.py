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

        asgi_dict = {
            'type': 'http',
            'asgi': {'version': '3.0'},
            'http_version': '1.1',
            'method': environ['REQUEST_METHOD'],
            'scheme': environ.get('wsgi.url_scheme', 'http'),
            'path': environ['PATH_INFO'],
            'query_string': environ.get('QUERY_STRING', '').encode(),
            'root_path': environ.get('SCRIPT_NAME', ''),
            'headers': self._get_headers(environ),
            'server': (environ.get('SERVER_NAME', 'localhost'),
                      int(environ.get('SERVER_PORT', 80))),
            'client': (environ.get('REMOTE_ADDR', 'localhost'), 0),
            'extensions': {},
        }

        body = self._read_body(environ)
        response_started = False
        response_data = BytesIO()

        async def receive():
            return {
                'type': 'http.request',
                'body': body,
                'more_body': False,
            }

        async def send(message):
            nonlocal response_started

            if message['type'] == 'http.response.start':
                response_started = True
                status = message['status']
                headers = [
                    (name.decode() if isinstance(name, bytes) else name,
                     value.decode() if isinstance(value, bytes) else value)
                    for name, value in message.get('headers', [])
                ]
                start_response(f'{status} OK', headers)

            elif message['type'] == 'http.response.body':
                body = message.get('body', b'')
                if body:
                    response_data.write(body)

        loop.run_until_complete(self.asgi_app(asgi_dict, receive, send))
        loop.close()

        response_data.seek(0)
        return [response_data.read()]

    @staticmethod
    def _get_headers(environ):
        headers = []
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').lower()
                headers.append([header_name.encode(), value.encode()])
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                header_name = key.replace('_', '-').lower()
                if value:
                    headers.append([header_name.encode(), value.encode()])
        return headers

    @staticmethod
    def _read_body(environ):
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            content_length = 0

        if content_length > 0:
            return environ['wsgi.input'].read(content_length)
        return b''


# Wrap ASGI app (FastAPI) for WSGI server (PythonAnywhere)
application = ASGItoWSGI(app)
