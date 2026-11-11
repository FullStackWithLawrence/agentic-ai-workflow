"""Test the version."""

# python stuff
import re
import unittest

from app.__version__ import __version__


class TestVersion(unittest.TestCase):
    """Test the version."""

    def test_version_is_semantic(self):
        """Test that semantic-release wrote a version like 1.2.3 or 1.2.3-alpha.1."""
        self.assertRegex(__version__, re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?$"))


if __name__ == "__main__":
    unittest.main()
