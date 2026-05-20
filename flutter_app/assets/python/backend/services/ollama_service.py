"""
Ollama Service - Manages local LLM model lifecycle and interactions.
Handles model initialization, pulling, health checks, and inference.
"""

import requests
import logging
import time
import subprocess
import platform
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── Constants ───
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_API_ENDPOINT = f"{OLLAMA_HOST}/api"
PRIMARY_MODEL = "mistral:7b"
MODEL_TIMEOUT = 300  # 5 minutes to pull/load model
HEALTH_CHECK_TIMEOUT = 30  # 30 seconds for health checks


class OllamaService:
    """Service for managing Ollama model lifecycle and inference."""

    def __init__(self, host: str = OLLAMA_HOST, model: str = PRIMARY_MODEL):
        """
        Initialize Ollama service.

        Args:
            host: Ollama API host (default: localhost:11434)
            model: Model name to use (default: mistral:7b)
        """
        self.host = host
        self.model = model
        self.api_endpoint = f"{host}/api"
        self.is_ready = False
        self.ollama_process = None

    # ─── Startup & Initialization ───
    def startup(self) -> bool:
        """
        Initialize Ollama and ensure model is ready.
        Called on Flask app startup.

        Returns:
            True if successful, False otherwise
        """
        logger.info("🚀 Starting Ollama service initialization...")

        try:
            # Step 1: Ensure Ollama is running
            if not self._ensure_ollama_running():
                logger.error("✗ Failed to start Ollama")
                return False

            # Step 2: Health check
            if not self._health_check():
                logger.error("✗ Ollama health check failed")
                return False

            # Step 3: Ensure model is pulled
            if not self._ensure_model_loaded():
                logger.error(f"✗ Failed to load model: {self.model}")
                return False

            # Step 4: Test inference (non-critical)
            if not self._test_inference():
                logger.warning(
                    "⚠️  Inference test failed, but marking as ready anyway"
                )
                # Don't fail just because inference test failed - might be a transient issue

            self.is_ready = True
            logger.info(f"✅ Ollama ready with {self.model}")
            return True

        except Exception as e:
            logger.error(f"✗ Ollama startup error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _ensure_ollama_running(self) -> bool:
        """
        Check if Ollama is running. If not, attempt to start it.

        Returns:
            True if Ollama is running or started, False otherwise
        """
        logger.info("Checking if Ollama is running...")

        # Try to connect
        if self._ping_ollama():
            logger.info("✓ Ollama already running")
            return True

        logger.info("Ollama not running - attempting to start...")

        try:
            # Platform-specific startup
            system = platform.system()

            if system == "Windows":
                # Try to start Ollama on Windows
                # Look for Ollama in common installation paths
                ollama_paths = [
                    r"C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama.exe",
                    r"C:\Program Files\Ollama\ollama.exe",
                ]

                for path in ollama_paths:
                    expanded_path = os.path.expandvars(path)
                    if os.path.exists(expanded_path):
                        logger.info(f"Starting Ollama from {expanded_path}")
                        subprocess.Popen(
                            [expanded_path, "serve"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        # Wait for startup
                        time.sleep(5)
                        if self._ping_ollama():
                            logger.info("✓ Ollama started successfully")
                            return True
                        break

            elif system in ["Darwin", "Linux"]:
                # macOS or Linux
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(5)
                if self._ping_ollama():
                    logger.info("✓ Ollama started successfully")
                    return True

            logger.error(
                "Could not start Ollama. Please ensure Ollama is installed "
                "and running: https://ollama.ai"
            )
            return False

        except Exception as e:
            logger.error(f"Error starting Ollama: {e}")
            return False

    def _ping_ollama(self) -> bool:
        """
        Ping Ollama to check if it's responsive.

        Returns:
            True if Ollama responds, False otherwise
        """
        try:
            response = requests.get(
                f"{self.api_endpoint}/tags", timeout=HEALTH_CHECK_TIMEOUT
            )
            return response.status_code == 200
        except Exception:
            return False

    def _health_check(self) -> bool:
        """
        Perform health check on Ollama.

        Returns:
            True if healthy, False otherwise
        """
        logger.info("Performing Ollama health check...")

        try:
            response = requests.get(
                f"{self.api_endpoint}/tags", timeout=HEALTH_CHECK_TIMEOUT
            )
            if response.status_code == 200:
                logger.info("✓ Ollama health check passed")
                return True
            else:
                logger.error(f"Health check returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def _ensure_model_loaded(self) -> bool:
        """
        Ensure the model is pulled and loaded.

        Returns:
            True if model is loaded, False otherwise
        """
        logger.info(f"Ensuring model {self.model} is loaded...")

        try:
            # Check if model exists
            if self._model_exists():
                logger.info(f"✓ Model {self.model} already exists")
                return True

            # Pull model
            logger.info(f"Pulling model {self.model}... (this may take a few minutes)")
            return self._pull_model()

        except Exception as e:
            logger.error(f"Error ensuring model loaded: {e}")
            return False

    def _model_exists(self) -> bool:
        """
        Check if model is already pulled.

        Returns:
            True if model exists, False otherwise
        """
        try:
            response = requests.get(f"{self.api_endpoint}/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                # Check if our model is in the list (exact or partial match)
                for name in model_names:
                    if self.model in name or name.startswith(self.model.split(":")[0]):
                        logger.info(f"✓ Found model: {name}")
                        return True
            return False
        except Exception as e:
            logger.error(f"Error checking model existence: {e}")
            return False

    def _pull_model(self) -> bool:
        """
        Pull (download) the model from Ollama registry.

        Returns:
            True if pull successful, False otherwise
        """
        try:
            logger.info(f"Starting model pull: {self.model}")
            response = requests.post(
                f"{self.api_endpoint}/pull",
                json={"name": self.model},
                timeout=MODEL_TIMEOUT,
                stream=False,
            )

            if response.status_code == 200:
                logger.info(f"✓ Model {self.model} pulled successfully")
                return True
            else:
                logger.error(f"Pull failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

        except requests.Timeout:
            logger.error(f"Model pull timeout (>{MODEL_TIMEOUT}s) - model too large?")
            return False
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False

    def _test_inference(self) -> bool:
        """
        Test inference with a simple prompt.

        Returns:
            True if inference works, False otherwise
        """
        try:
            logger.info("Testing inference with simple prompt...")
            response = requests.post(
                f"{self.api_endpoint}/generate",
                json={
                    "model": self.model,
                    "prompt": "Say 'ready' in one word.",
                    "stream": False,
                },
                timeout=60,
            )

            if response.status_code == 200:
                logger.info("✓ Inference test successful")
                return True
            else:
                logger.error(f"Inference test failed with status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error testing inference: {e}")
            return False

    # ─── Inference ───
    def generate(self, prompt: str, stream: bool = False) -> dict:
        """
        Generate text using the model.

        Args:
            prompt: Input prompt
            stream: Whether to stream response

        Returns:
            Response dict with 'response' and 'done' keys
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": "Ollama not ready. Call startup() first.",
            }

        try:
            response = requests.post(
                f"{self.api_endpoint}/generate",
                json={"model": self.model, "prompt": prompt, "stream": stream},
                timeout=120,
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                logger.error(f"Generation failed: {response.status_code}")
                return {"success": False, "error": "Generation failed"}

        except Exception as e:
            logger.error(f"Error generating: {e}")
            return {"success": False, "error": str(e)}

    # ─── Shutdown ───
    def shutdown(self) -> bool:
        """
        Gracefully shutdown Ollama.
        Called on Flask app shutdown.

        Returns:
            True if successful
        """
        logger.info("🛑 Shutting down Ollama service...")

        try:
            self.is_ready = False
            logger.info("✓ Ollama service shutdown complete")
            return True

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            return False

    # ─── Status ───
    def get_status(self) -> dict:
        """
        Get current status of Ollama service.

        Returns:
            Status dict with health and model info
        """
        return {
            "is_ready": self.is_ready,
            "model": self.model,
            "host": self.host,
            "health": self._ping_ollama(),
        }


# ─── Global Singleton Instance ───
_ollama_service = None


def get_ollama_service() -> OllamaService:
    """Get the global Ollama service instance."""
    global _ollama_service
    if _ollama_service is None:
        logger.warning("⚠️  Creating NEW Ollama service instance (this should only happen once at startup)")
        _ollama_service = OllamaService()
    logger.warning(f"get_ollama_service() returning instance {id(_ollama_service)} - is_ready={_ollama_service.is_ready}, model={_ollama_service.model if hasattr(_ollama_service, 'model') else 'N/A'}")
    return _ollama_service
