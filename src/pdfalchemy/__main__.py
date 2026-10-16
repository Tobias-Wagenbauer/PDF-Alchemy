"""Entry point for ``python -m pdfalchemy``."""

from __future__ import annotations

import sys

from pdfalchemy.app import run

if __name__ == "__main__":
    sys.exit(run())
