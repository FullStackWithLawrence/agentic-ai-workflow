# pylint: disable=wrong-import-position
"""Test settings."""

# python stuff
import importlib
import os
import unittest
from unittest.mock import patch

from app import settings
from app.exceptions import ConfigurationException

COMPLETE_ENVIRONMENT = {
    "OPENAI_API_KEY": "test-key",
    "MYSQL_HOST": "127.0.0.1",
    "MYSQL_USER": "smarter_test_user",
    "MYSQL_PASSWORD": "smarter_test_user",
    "MYSQL_DATABASE": "smarter_test_db",
}


def reload_settings(environment: dict[str, str]) -> None:
    """Import app.settings again, with only these environment variables, and without .env."""
    with patch.dict(os.environ, environment, clear=True), patch("dotenv.load_dotenv"):
        importlib.reload(settings)


class TestSettings(unittest.TestCase):
    """Test settings."""

    def tearDown(self):
        """Import app.settings again from the real environment, for the other tests."""
        importlib.reload(settings)

    def test_complete_settings(self):
        """Test the settings, and their defaults."""
        reload_settings(COMPLETE_ENVIRONMENT)
        self.assertEqual(settings.MYSQL_HOST, "127.0.0.1")
        self.assertEqual(settings.MYSQL_PORT, 3306)
        self.assertEqual(settings.MYSQL_CHARSET, "utf8mb4")
        self.assertEqual(settings.OPENAI_API_MODEL, "gpt-4o-mini")

    def test_missing_mysql_setting(self):
        """Test that a missing MySQL setting stops the app."""
        environment = {k: v for k, v in COMPLETE_ENVIRONMENT.items() if k != "MYSQL_HOST"}
        with self.assertRaises(ConfigurationException):
            reload_settings(environment)

    def test_missing_openai_api_key(self):
        """Test that a missing OpenAI API key stops the app."""
        environment = {k: v for k, v in COMPLETE_ENVIRONMENT.items() if k != "OPENAI_API_KEY"}
        with self.assertRaises(ConfigurationException):
            reload_settings(environment)


if __name__ == "__main__":
    unittest.main()
