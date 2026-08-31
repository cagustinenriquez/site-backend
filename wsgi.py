"""
WSGI entry point for PythonAnywhere deployment.
"""
import os
import sys

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Import FastAPI app and Starlette's WSGI middleware
from main import app
from starlette.middleware.wsgi import WSGIMiddleware

# Wrap the FastAPI ASGI app as a WSGI middleware
# This converts it to WSGI for PythonAnywhere compatibility
application = WSGIMiddleware(app)
