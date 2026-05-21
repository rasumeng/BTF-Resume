"""
Backend Runner for BT-Resume

Entry point for the Flask backend when bundled with the standalone Flutter app.
Adds core/ and backend/ parent directory to sys.path so imports (from core.*, from backend.*) resolve correctly.
"""

import sys
import os

# Add the parent directory (Documents/BTFResume/) so both backend/ and core/ are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
