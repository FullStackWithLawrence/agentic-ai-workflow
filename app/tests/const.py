# -*- coding: utf-8 -*-
"""
Common constants for untit tests.
"""

import os
import sys
from pathlib import Path


HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = str(Path(HERE).parent.parent)
PYTHON_ROOT = str(Path(PROJECT_ROOT).parent)
if PYTHON_ROOT not in sys.path:
    sys.path.append(PYTHON_ROOT)  # noqa: E402

__all__ = ["HERE", "PROJECT_ROOT", "PYTHON_ROOT"]
