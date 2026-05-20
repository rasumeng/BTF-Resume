"""
Flask Backend for BT-Resume - Local AI Service Layer
Manages all resume processing and API endpoints.
"""

import logging
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import atexit
from pathlib import Path

# ─── Setup Logging (BEFORE any other imports) ───
# Suppress verbose Flask/Werkzeug logs - only show critical info
logging.basicConfig(
    level=logging.WARNING,  # Only show WARNING and ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # Force reconfiguration even if already configured
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Our app logs at INFO level

# Suppress Flask and Werkzeug debug logging (users don't need to see these)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)  # Only show werkzeug errors
flask_logger = logging.getLogger('flask')
flask_logger.setLevel(logging.ERROR)  # Only show flask errors
flask_logger.propagate = False

# Add core module to path
core_path = Path(__file__).parent.parent / "core"
sys.path.insert(0, str(core_path))

from config import FLASK_HOST, FLASK_PORT, OLLAMA_HOST, get_resumes_dir, get_outputs_dir
from services.ollama_service import get_ollama_service

# ─── Initialize Required Directories ───
logger.info("=" * 60)
logger.info("📁 Initializing application directories...")
logger.info("=" * 60)

try:
    resumes_dir = get_resumes_dir()
    logger.info(f"✓ Resumes directory ready: {resumes_dir}")
    
    outputs_dir = get_outputs_dir()
    logger.info(f"✓ Outputs directory ready: {outputs_dir}")
except Exception as e:
    logger.error(f"✗ Failed to initialize directories: {e}")
    sys.exit(1)

# ─── Flask App Setup ───
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ─── Ollama Service Initialization ───
ollama_service = get_ollama_service()
logger.info(f"app.py: Got Ollama service instance {id(ollama_service)}")


def initialize_ollama():
    """Initialize Ollama service. Called by run_backend.py."""
    logger.info("=" * 60)
    logger.info("🚀 Initializing Ollama LLM Service from app.py...")
    logger.info(f"Service instance ID: {id(ollama_service)}")
    logger.info("=" * 60)
    
    logger.info(f"Before startup: is_ready={ollama_service.is_ready}")
    success = ollama_service.startup()
    logger.info(f"After startup: is_ready={ollama_service.is_ready}, success={success}")
    
    if success:
        logger.info("✅ Ollama service initialized successfully in app!")
        logger.info(f"Ollama is_ready flag: {ollama_service.is_ready}")
        return True
    else:
        logger.warning(
            "⚠️  Ollama service failed to initialize. "
            "Please ensure Ollama is installed and running: https://ollama.ai"
        )
        logger.info(f"Ollama is_ready flag: {ollama_service.is_ready}")
        return False


@app.before_request
def inject_ollama_service():
    """Inject Ollama service into request context."""
    from flask import g
    logger.debug(f"before_request: injecting ollama_service instance {id(ollama_service)} with is_ready={ollama_service.is_ready}")
    g.ollama_service = ollama_service
    logger.debug(f"before_request: g.ollama_service is now {id(g.ollama_service)} with is_ready={g.ollama_service.is_ready}")


# ─── Health Check Endpoint (Critical for Startup) ───
@app.route("/api/health", methods=["GET"])
def health():
    """
    Health check endpoint - used by Flutter to verify backend is ready.
    This should be the FIRST thing Flutter checks when launching.
    """
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "resume-ai-api",
            "llm_ready": ollama_service.is_ready,
        }
    )


# ─── Status Endpoint ───
@app.route("/api/status", methods=["GET"])
def status():
    """Get detailed status of all services."""
    return jsonify(
        {
            "api": "running",
            "ollama": ollama_service.get_status(),
            "ollama_is_ready": ollama_service.is_ready,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


# ─── Register Route Blueprints ───
try:
    from routes.resume_routes import resume_bp
    
    logger.info(f"resume_bp type: {type(resume_bp)}")
    logger.info(f"resume_bp routes: {resume_bp.deferred_functions if hasattr(resume_bp, 'deferred_functions') else 'N/A'}")

    app.register_blueprint(resume_bp, url_prefix="/api")
    logger.info("✓ Registered resume routes")
    
    # Debug: Print all registered routes
    logger.info("=== ALL REGISTERED ROUTES ===")
    for rule in app.url_map.iter_rules():
        logger.info(f"  {rule.rule} -> {rule.endpoint}")
except Exception as e:
    logger.error(f"✗ Failed to register resume routes: {e}")
    import traceback
    logger.error(traceback.format_exc())


# ─── Error Handlers ───
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "error": "Bad request"}), 400


@app.errorhandler(404)
def not_found(error):
    logger.error(f"404 NOT FOUND: {request.path} - {error}")
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    logger.error(f"SERVER ERROR HANDLER: {error}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    return jsonify({"success": False, "error": "Internal server error"}), 500


# ─── Startup & Shutdown Handlers ───
def startup_ollama():
    """Initialize Ollama service on app startup."""
    logger.info("=" * 60)
    logger.info("🚀 Initializing Ollama LLM Service...")
    logger.info("=" * 60)

    if ollama_service.startup():
        logger.info("✅ Ollama service initialized successfully!")
    else:
        logger.warning(
            "⚠️  Ollama service failed to initialize. "
            "Please ensure Ollama is installed and running: https://ollama.ai"
        )


def shutdown_ollama():
    """Gracefully shutdown Ollama service on app shutdown."""
    logger.info("=" * 60)
    logger.info("🛑 Shutting down Ollama LLM Service...")
    logger.info("=" * 60)
    ollama_service.shutdown()
    logger.info("✓ Ollama service shutdown complete")


# ─── Startup ───
if __name__ == "__main__":
    logger.info(f"🚀 Starting Resume AI Backend on {FLASK_HOST}:{FLASK_PORT}")
    logger.info(f"📁 Resumes directory: {get_resumes_dir()}")

    # Initialize Ollama on startup
    startup_ollama()

    # Register shutdown handler
    atexit.register(shutdown_ollama)

    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("✓ Shutdown signal received")
    finally:
        shutdown_ollama()