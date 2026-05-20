"""
DEPRECATED: This module is maintained for backward compatibility.
Please import from core.pdf instead.

Example:
    from core.pdf import generate_pdf
"""

import warnings

warnings.warn(
    "core.pdf_generator is deprecated. "
    "Please use core.pdf instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new locations for backward compatibility
from core.pdf import generate_pdf

__all__ = ["generate_pdf"]
