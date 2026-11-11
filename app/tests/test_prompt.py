# pylint: disable=wrong-import-position
# pylint: disable=R0801,C0115,W0613
"""Test prompt."""

# python stuff
import unittest
from unittest.mock import MagicMock, patch

import httpx
import openai
from openai.types.chat import ChatCompletion

from app import prompt, settings


class DummyResponse:
    def __init__(self):
        self.request = None
        self.status_code = None
        self.headers = {}
        self.body = b""


dummy_request = httpx.Request("GET", "https://example.com")
dummy_response = DummyResponse()


def make_completion(content: str | None, tool_calls: list[dict] | None = None) -> ChatCompletion:
    """Return a ChatCompletion like the ones the OpenAI API returns."""
    message: dict = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return ChatCompletion.model_validate(
        {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 0,
            "model": "gpt-6-luna",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "tool_calls" if tool_calls else "stop",
                    "message": message,
                }
            ],
        }
    )


def make_tool_call(name: str, arguments: str, call_id: str = "call_1") -> dict:
    """Return a function tool call, as it appears in a ChatCompletion."""
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


class TestPrompt(unittest.TestCase):
    """Test prompt."""

    def setUp(self):
        """Keep each test's messages out of the shared conversation."""
        self.saved_messages = list(prompt.messages)

    def tearDown(self):
        """Restore the shared conversation."""
        prompt.messages[:] = self.saved_messages

    def test_process_tool_calls(self):
        """Test that a tool call is run and its result added to the conversation."""
        message = (
            make_completion(None, [make_tool_call("get_courses", '{"description": "AI", "max_cost": 500}')])
            .choices[0]
            .message
        )
        with patch("app.prompt.handle_function_call", return_value='[{"course_code": "AI101"}]') as mock_handle:
            functions_called = prompt.process_tool_calls(message)

        self.assertEqual(functions_called, ["get_courses"])
        mock_handle.assert_called_once_with("get_courses", {"description": "AI", "max_cost": 500})
        assistant_message, tool_message = prompt.messages[-2], prompt.messages[-1]
        self.assertEqual(assistant_message["role"], "assistant")
        self.assertEqual(assistant_message["content"], "Accessing tool...")
        self.assertEqual(assistant_message["tool_calls"][0]["function"]["name"], "get_courses")
        self.assertEqual(tool_message["role"], "tool")
        self.assertEqual(tool_message["tool_call_id"], "call_1")
        self.assertEqual(tool_message["content"], '[{"course_code": "AI101"}]')

    def test_process_tool_calls_keeps_content(self):
        """Test that the model's own text is kept with its tool call."""
        message = (
            make_completion("Let me look that up.", [make_tool_call("register_course", '{"course_code": "CS107"}')])
            .choices[0]
            .message
        )
        with patch("app.prompt.handle_function_call", return_value='{"success": true}'):
            functions_called = prompt.process_tool_calls(message)

        self.assertEqual(functions_called, ["register_course"])
        self.assertEqual(prompt.messages[-2]["content"], "Let me look that up.")

    def test_completion_runs_tool_calls(self):
        """Test that completion runs the model's tool calls, then returns its answer."""
        responses = [
            make_completion(None, [make_tool_call("get_courses", "{}")]),
            make_completion("Here are the courses."),
        ]
        with (
            patch("app.prompt.openai.chat.completions.create", side_effect=responses) as mock_create,
            patch("app.prompt.handle_function_call", return_value="[]"),
        ):
            response, functions_called = prompt.completion("Show me the courses.")

        self.assertEqual(response.choices[0].message.content, "Here are the courses.")
        self.assertEqual(functions_called, ["get_courses"])
        self.assertEqual(mock_create.call_count, 2)
        # The second call offers both tools, and lets the model choose.
        second_call = mock_create.call_args_list[1].kwargs
        self.assertEqual(len(second_call["tools"]), 2)
        self.assertEqual(second_call["tool_choice"], "auto")
        # Reasoning models need these instead of max_tokens and default reasoning.
        self.assertEqual(second_call["max_completion_tokens"], settings.OPENAI_API_MAX_TOKENS)
        self.assertEqual(second_call["reasoning_effort"], "none")

    def test_completion_stops_on_goodbye(self):
        """Test that completion stops at "Goodbye!" even when the model also calls a tool."""
        goodbye = make_completion("Goodbye!", [make_tool_call("get_courses", "{}")])
        with (
            patch("app.prompt.openai.chat.completions.create", return_value=goodbye) as mock_create,
            patch("app.prompt.handle_function_call") as mock_handle,
        ):
            response, functions_called = prompt.completion("That's all, thanks.")

        self.assertIs(response, goodbye)
        self.assertEqual(functions_called, [])
        mock_create.assert_called_once()
        mock_handle.assert_not_called()

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
        side_effect=openai.RateLimitError(message="rate limit", response=dummy_response, body=None),  # type: ignore
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
        side_effect=openai.AuthenticationError(
            message="auth error", response=dummy_response, body=None  # type: ignore
        ),
    )
    def test_handle_completion_authentication_error(self, mock_create):
        """Test that authentication errors during completion are handled."""
        with self.assertRaises(openai.AuthenticationError):
            prompt.completion("test prompt")

    @patch(
        "app.prompt.openai.chat.completions.create",
        side_effect=openai.BadRequestError(message="bad request", response=dummy_response, body=None),  # type: ignore
    )
    def test_handle_completion_bad_request_error(self, mock_create):
        """Test that bad request errors during completion are handled."""
        with self.assertRaises(openai.BadRequestError):
            prompt.completion("test prompt")

    @patch(
        "app.prompt.openai.chat.completions.create",
        side_effect=openai.APIError(dummy_request, "api error", body=None),  # type: ignore
    )
    def test_handle_completion_api_error(self, mock_create):
        """Test that API errors during completion are handled."""
        with self.assertRaises(openai.APIError):
            prompt.completion("test prompt")
