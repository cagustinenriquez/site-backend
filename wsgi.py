"""
WSGI entry point for PythonAnywhere deployment.
"""
import os
import sys

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Import and expose the FastAPI app
from main import app

# WSGI application
application = app
