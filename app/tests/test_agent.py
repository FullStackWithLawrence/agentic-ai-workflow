# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# pylint: disable=R0801,C0115,W0613
"""Test application."""

# python stuff
import unittest
from unittest.mock import patch

from app import agent
from app.agent import main  # noqa: E402


class TestApplication(unittest.TestCase):
    """Test application."""

    def test_application_does_not_crash(self):
        """Test that the application returns a value."""

        # pylint: disable=broad-exception-caught
        prompts = (
            "Show me a list of available courses.",
            "I would like to register for the CS107 Algorithms course. My name is John Doe and my email is john.doe@example.com",
            "Thank you, that's all for now. Goodbye!",
            "Goodbye!",
            "Go away!",
        )
        try:
            main(prompts=prompts)
        except Exception as e:
            self.fail(f"main raised an exception: {e}")

    @patch("app.agent.completion")
    @patch("builtins.input", return_value="no")
    def test_main_goodbye(self, mock_input, mock_completion):
        """Test that the application exits on "Goodbye!"."""
        mock_completion.return_value = (None, [])
        agent.main(prompts=("no",))

    @patch("app.agent.completion")
    @patch("builtins.input", side_effect=["yes", "no"])
    def test_main_followup_question(self, mock_input, mock_completion):
        """Test that the application handles a follow-up question."""

        class MockMessage:
            content = "Some info\nQUESTION: What would you like to do next?"

        class MockResponse:
            choices = [type("obj", (), {"message": MockMessage})]

        mock_completion.side_effect = [
            (MockResponse(), ["get_courses"]),
            (MockResponse(), ["register_course"]),
            (None, []),
        ]
        agent.main(prompts=None)

    @patch("app.agent.completion")
    @patch("builtins.input", side_effect=["something", "no"])
    def test_main_default_prompt(self, mock_input, mock_completion):
        """Test that the application handles a default prompt."""

        class MockMessage:
            content = "Just a message"

        class MockResponse:
            choices = [type("obj", (), {"message": MockMessage})]

        mock_completion.side_effect = [(MockResponse(), []), (None, [])]
        agent.main(prompts=None)
