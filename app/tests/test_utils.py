# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# pylint: disable=R0801,C0115
"""Test utils."""

# python stuff
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from app import utils


HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = str(Path(HERE).parent.parent)
PYTHON_ROOT = str(Path(PROJECT_ROOT).parent)
if PYTHON_ROOT not in sys.path:
    sys.path.append(PYTHON_ROOT)  # noqa: E402


class TestUtils(unittest.TestCase):
    """Test utils."""

    def test_application_does_not_crash(self):
        """Test utils."""

    def test_color_text_supported_color(self):
        """Test that color_text works with supported colors."""
        result = utils.color_text("hello", "green")
        self.assertIn("\033[", result)
        self.assertIn("hello", result)

    def test_dump_json_colored_not_serializable(self):
        """Test that dump_json_colored raises TypeError for non-serializable data."""

        class NotSerializable:
            pass

        with self.assertRaises(TypeError):
            utils.dump_json_colored(NotSerializable(), "red")

    def test_color_text_unsupported_color(self):
        """Test that color_text raises ValueError for unsupported colors."""

        with self.assertRaises(ValueError):
            utils.color_text("hello", "notacolor")

    def test_dump_json_colored_typeerror(self):
        """Test that dump_json_colored raises TypeError for non-serializable data."""

        class NotSerializable:
            pass

        # Use a supported color to reach the serialization error branch
        with self.assertRaises(TypeError) as ctx:
            utils.dump_json_colored(NotSerializable(), "blue")
        self.assertIn("Data is not JSON serializable", str(ctx.exception))
