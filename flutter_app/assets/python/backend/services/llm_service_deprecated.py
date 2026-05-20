"""
DEPRECATED: This module is maintained for backward compatibility.
Please import from backend.services.llm instead.

Example:
    from backend.services.llm import LLMService
    from backend.services.llm.parsers import extract_json_from_response
"""

import warnings

warnings.warn(
    "backend.services.llm_service is deprecated. "
    "Please use backend.services.llm instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new locations for backward compatibility
from services.llm import LLMService
from services.llm.parsers import extract_json_from_response as _extract_json_from_response

__all__ = ["LLMService", "_extract_json_from_response"]
