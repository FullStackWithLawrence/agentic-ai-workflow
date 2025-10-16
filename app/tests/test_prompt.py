# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# pylint: disable=R0801,C0115,W0613
"""Test prompt."""

# python stuff
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import openai

from app import prompt


HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = str(Path(HERE).parent.parent)
PYTHON_ROOT = str(Path(PROJECT_ROOT).parent)
if PYTHON_ROOT not in sys.path:
    sys.path.append(PYTHON_ROOT)  # noqa: E402


class DummyResponse:
    def __init__(self):
        self.request = None
        self.status_code = None
        self.headers = {}
        self.body = b""


dummy_request = httpx.Request("GET", "https://example.com")
dummy_response = DummyResponse()


class TestPrompt(unittest.TestCase):
    """Test prompt."""

    def test_handle_function_call_get_courses(self):
        """Test that get_courses function call is handled correctly."""
        with patch("app.prompt.stackademy_app.get_courses", return_value=[{"course_code": "TEST"}]):
            result = prompt.handle_function_call("get_courses", {"description": "test"})
            self.assertIn("TEST", result)

    def test_handle_function_call_register_course(self):
        """Test that register_course function call is handled correctly."""
        with patch("app.prompt.stackademy_app.register_course", return_value=True):
            result = prompt.handle_function_call(
                "register_course", {"course_code": "TEST", "email": "a@b.com", "full_name": "Test User"}
            )
            self.assertIn("success", result)

    def test_handle_function_call_unknown(self):
        """Test that unknown function call is handled correctly."""
        result = prompt.handle_function_call("unknown_func", {})
        self.assertIn("Unknown function", result)

    def test_process_tool_calls_empty(self):
        """Test that processing empty tool calls returns an empty list."""
        msg = MagicMock()
        msg.tool_calls = None
        self.assertEqual(prompt.process_tool_calls(msg), [])

    def test_completion_empty_prompt(self):
        """Test that completion with empty prompt returns None and empty list."""
        response, functions_called = prompt.completion("")
        self.assertIsNone(response)
        self.assertEqual(functions_called, [])

    def test_completion_return(self):
        """Test that completion returns a response and functions called."""
        with (
            patch("app.prompt.handle_function_call", return_value='{"success": true}'),
            patch("app.prompt.stackademy_app.tool_factory_get_courses", return_value={"tool": "get_courses"}),
            patch("app.prompt.stackademy_app.tool_factory_register", return_value={"tool": "register_course"}),
            patch("app.prompt.openai.chat.completions.create") as mock_create,
        ):
            # Simulate OpenAI response with no tool_calls
            class Msg:
                content = "Goodbye!"
                tool_calls = None

            class Choice:
                message = Msg()

            class Resp:
                choices = [Choice()]

                def model_dump(self):
                    """Dump the model data."""
                    return {"choices": [{"message": {"content": "Goodbye!", "tool_calls": None}}]}

            mock_create.return_value = Resp()
            response, functions_called = prompt.completion("test prompt")
            self.assertIsNotNone(response)
            self.assertIsInstance(functions_called, list)

    @patch("app.prompt.completion")
    def test_completion_loop_with_tool_calls(self, mock_completion):
        """Test that completion handles multiple tool calls and exits on "Goodbye!"."""

        class MockToolCall:
            type = "function"
            function = MagicMock()
            function.name = "get_courses"
            function.arguments = '{"description": "test"}'
            id = "tool1"

        class MockMessage:
            content = "Some response"
            tool_calls = [MockToolCall()]

        class MockChoice:
            message = MockMessage()

        class MockResponse:
            choices = [MockChoice()]

        # Patch handle_completion to simulate multiple tool calls
        with (
            patch("app.prompt.handle_function_call", return_value='{"success": true}'),
            patch("app.prompt.stackademy_app.tool_factory_get_courses", return_value={"tool": "get_courses"}),
            patch("app.prompt.stackademy_app.tool_factory_register", return_value={"tool": "register_course"}),
        ):
            # Patch the inner handle_completion to break after one loop
            def side_effect(*args, **kwargs):
                class Msg:
                    content = "Goodbye!"
                    tool_calls = None

                class Choice:
                    message = Msg()

                class Resp:
                    choices = [Choice()]

                return (Resp(), ["get_courses"])

            mock_completion.side_effect = [(MockResponse(), ["get_courses"]), side_effect()]
            response, functions_called = prompt.completion("test prompt")
            self.assertIsNotNone(response)
            self.assertIsInstance(functions_called, list)

    @patch("app.prompt.openai.chat.completions.create", side_effect=Exception("unexpected"))
    def test_handle_completion_unexpected_error(self, mock_create):
        """Test that unexpected errors during completion are handled."""
        with self.assertRaises(Exception):
            prompt.completion("test prompt")

    @patch(
        "app.prompt.openai.chat.completions.create",
        side_effect=openai.RateLimitError(message="rate limit", response=dummy_response, body=None),
    )
    def test_handle_completion_rate_limit_error(self, mock_create):
        """Test that rate limit errors during completion are handled."""
        with self.assertRaises(openai.RateLimitError):
            prompt.completion("test prompt")

    @patch(
        "app.prompt.openai.chat.completions.create",
        side_effect=openai.APIConnectionError(message="api connection", request=dummy_request),
    )
    def test_handle_completion_api_connection_error(self, mock_create):
        """Test that API connection errors during completion are handled."""
        with self.assertRaises(openai.APIConnectionError):
            prompt.completion("test prompt")

    @patch(
        "app.prompt.openai.chat.completions.create",
        side_effect=openai.AuthenticationError(message="auth error", response=dummy_response, body=None),
    )
    def test_handle_completion_authentication_error(self, mock_create):
        """Test that authentication errors during completion are handled."""
        with self.assertRaises(openai.AuthenticationError):
            prompt.completion("test prompt")

    @patch(
        "app.prompt.openai.chat.completions.create",
        side_effect=openai.BadRequestError(message="bad request", response=dummy_response, body=None),
    )
    def test_handle_completion_bad_request_error(self, mock_create):
        """Test that bad request errors during completion are handled."""
        with self.assertRaises(openai.BadRequestError):
            prompt.completion("test prompt")

    @patch(
        "app.prompt.openai.chat.completions.create", side_effect=openai.APIError(dummy_request, "api error", body=None)
    )
    def test_handle_completion_api_error(self, mock_create):
        """Test that API errors during completion are handled."""
        with self.assertRaises(openai.APIError):
            prompt.completion("test prompt")
