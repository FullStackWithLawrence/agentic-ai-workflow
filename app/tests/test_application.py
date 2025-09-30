# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# pylint: disable=R0801
"""Test application."""

# python stuff
import os
import sys
import unittest
from pathlib import Path

from app.agent import main  # noqa: E402


HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = str(Path(HERE).parent.parent)
PYTHON_ROOT = str(Path(PROJECT_ROOT).parent)
if PYTHON_ROOT not in sys.path:
    sys.path.append(PYTHON_ROOT)  # noqa: E402


class TestApplication(unittest.TestCase):
    """Test application."""

    def test_application_does_not_crash(self):
        """Test that the application returns a value."""

        # pylint: disable=broad-exception-caught
        try:
            main()
        except Exception as e:
            self.fail(f"main raised an exception: {e}")
