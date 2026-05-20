"""
Backend configuration for BT-Resume.
Handles ports, paths, and environment setup.
"""

import os
import platform
from pathlib import Path

# ─── Flask Configuration ───
FLASK_HOST = "127.0.0.1"  # Only localhost (secure for local app)
FLASK_PORT = 5000
FLASK_DEBUG = True

# ─── Ollama Configuration ───
OLLAMA_HOST = "http://localhost:11434"

# ─── Paths ───
def get_app_data_dir():
    r"""Get the user's app data directory (platform-specific).
    Windows: C:\Users\<User>\Documents\BT-Resume
    macOS: ~/Documents/BT-Resume
    Linux: ~/.local/share/BT-Resume
    """
    if platform.system() == "Windows":
        # Use Documents folder on Windows
        user_home = Path(os.path.expanduser("~"))
        app_data = user_home / "Documents" / "BT-Resume"
    elif platform.system() == "Darwin":  # macOS
        user_home = Path(os.path.expanduser("~"))
        app_data = user_home / "Documents" / "BT-Resume"
    else:  # Linux and others
        user_home = Path(os.path.expanduser("~"))
        app_data = user_home / ".local" / "share" / "BT-Resume"
    
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data

def get_base_dir():
    """Get the base directory of the project."""
    return Path(__file__).parent.parent

def get_resumes_dir():
    """Get the resumes directory in user's app data."""
    app_data = get_app_data_dir()
    resumes_dir = app_data / "resumes"
    resumes_dir.mkdir(parents=True, exist_ok=True)
    return resumes_dir

def get_outputs_dir():
    """Get the outputs directory in user's app data."""
    app_data = get_app_data_dir()
    outputs_dir = app_data / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    return outputs_dir

def get_models_dir():
    """Get the models directory."""
    base_dir = get_base_dir()
    models_dir = base_dir / "models"
    models_dir.mkdir(exist_ok=True)
    return models_dir

# ─── Models ───
MODELS = {
    "polish": "mistral:7b",      # Fast, good for bullet polish
    "tailor": "mistral:7b",      # Mistral for consistent performance across all tasks
    "grade": "mistral:7b",       # Mistral for resume grading
    "parse": "mistral:7b",       # Mistral for parsing resume data
}

# ─── Response Schema Defaults ───
DEFAULT_RESPONSE = {
    "success": True,
    "data": None,
    "error": None,
    "timestamp": None
}
