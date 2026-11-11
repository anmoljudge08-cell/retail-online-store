"""Vercel entrypoint.

Vercel's Python runtime looks for a module-level WSGI `app`. The storefront lives
in the repository root, so add it to sys.path before importing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402,F401  (exported for the WSGI runtime)
