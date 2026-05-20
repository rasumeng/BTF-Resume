"""
WSGI entry point for Gunicorn.
Run with: gunicorn --bind 127.0.0.1:5000 backend.wsgi:app
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    app.run()
