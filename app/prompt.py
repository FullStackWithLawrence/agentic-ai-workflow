# -*- coding: utf-8 -*-
"""
Prompt engineering and management for Stackademy.
Handles function calling and response parsing.
"""

import json
from typing import Optional, Union

import openai
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageFunctionToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

from app import settings
from app.const import MISSING, ToolChoice
from app.logging_config import get_logger, setup_logging
from app.settings import LLM_ASSISTANT_NAME, LLM_TOOL_CHOICE
from app.stackademy import stackademy_app
from app.utils import dump_json_colored


setup_logging()
logger = get_logger(__name__)

MessagesType = list[
    Union[
        ChatCompletionSystemMessageParam,
        ChatCompletionUserMessageParam,
        ChatCompletionAssistantMessageParam,
        ChatCompletionToolMessageParam,
    ]
]

messages: MessagesType = [
    ChatCompletionSystemMessageParam(
        role="system",
        content="""You are a helpful assistant for the Stackademy online learning platform.
            If the user wants no further assistance, respond with "Goodbye!".
            Prioritize use of the functions available to you as needed.
            Do not provide answers that are not based on the functions available to you.
            Your task is to assist users with their queries related to the platform,
            including course information, enrollment procedures, and general support.
            You should respond in a concise and clear manner, providing accurate information based on the user's request.
            If you ask a follow up question, then place it at the bottom of the response and precede it with "QUESTION:".
            """,
        name=LLM_ASSISTANT_NAME,
    ),
    ChatCompletionAssistantMessageParam(
        role="assistant",
        content="How can I assist you with Stackademy today?",
        name=LLM_ASSISTANT_NAME,
    ),
]


def handle_function_call(function_name: str, arguments: dict) -> str:
    """Handle function calls from the OpenAI API."""
    if function_name == "get_courses":
        # Extract parameters with defaults
        description = arguments.get("description")
        max_cost = arguments.get("max_cost")

        # Call the actual function
        courses = stackademy_app.get_courses(description=description, max_cost=max_cost)

        # Return as JSON string
        return json.dumps(courses, default=str, indent=2)

    if function_name == "register_course":
        course_code = arguments.get("course_code", MISSING)
        email = arguments.get("email", MISSING)
        full_name = arguments.get("full_name", MISSING)

        # Call the actual function
        success = stackademy_app.register_course(course_code=course_code, email=email, full_name=full_name)

        # Return result as JSON string
        return json.dumps({"success": success})

    return json.dumps({"error": f"Unknown function: {function_name}"})


def process_tool_calls(message: ChatCompletionMessage) -> list[str]:
    """Process tool calls in the messages list."""
    functions_called = []
    if not isinstance(message, ChatCompletionMessage) or not message.tool_calls:
        return functions_called
    for tool_call in message.tool_calls:

        if tool_call.type == "function":
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            functions_called.append(function_name)
            tool_calls_param = [
                ChatCompletionMessageFunctionToolCallParam(
                    id=tool_call.id,
                    type="function",
                    function={
                        "name": function_name,
                        "arguments": tool_call.function.arguments,
                    },
                )
            ]
            assistant_content = message.content if message.content else "Accessing tool..."
            messages.append(
                ChatCompletionAssistantMessageParam(
                    role="assistant", content=assistant_content, tool_calls=tool_calls_param, name=LLM_ASSISTANT_NAME
                )
            )
            logger.info("Function call detected: %s with args %s", function_name, function_args)

            function_result = handle_function_call(function_name, function_args)

            tool_message = ChatCompletionToolMessageParam(
                role="tool", content=function_result, tool_call_id=tool_call.id
            )
            messages.append(tool_message)

        logger.debug(
            "Updated messages: %s",
            [dump_json_colored(msg.model_dump(), "blue") if not isinstance(msg, dict) else msg for msg in messages],
        )
    return functions_called


def completion(prompt: str) -> tuple[Optional[ChatCompletion], list[str]]:
    """LLM text completion"""

    def handle_completion(tools, tool_choice) -> ChatCompletion:
        """Handle the OpenAI chat completion call."""
        openai.api_key = settings.OPENAI_API_KEY
        model = settings.OPENAI_API_MODEL

        try:
            logger.debug(
                "Sending messages to OpenAI: %s %s",
                dump_json_colored(messages, "blue"),
                dump_json_colored(tools, "blue"),
            )
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=settings.OPENAI_API_TEMPERATURE,
                max_tokens=settings.OPENAI_API_MAX_TOKENS,
            )
            logger.debug("OpenAI response: %s", dump_json_colored(response.model_dump(), "green"))
            return response
        except openai.RateLimitError as e:
            logger.error("OpenAI rate limit exceeded: %s", e)
            raise
        except openai.APIConnectionError as e:
            logger.error("OpenAI API connection error: %s", e)
            raise
        except openai.AuthenticationError as e:
            logger.error("OpenAI authentication error: %s", e)
            raise
        except openai.BadRequestError as e:
            logger.error("OpenAI bad request error: %s", e)
            raise
        except openai.APIError as e:
            logger.error("OpenAI API error: %s", e)
            raise
        # pylint: disable=broad-except
        except Exception as e:
            logger.error("Unexpected error during OpenAI completion: %s", e)
            raise

    if not prompt.strip():
        logger.warning("Received empty prompt.")
        return None, []

    messages.append(ChatCompletionUserMessageParam(role="user", content=prompt))
    functions_called = []

    response = handle_completion(
        # tool_choice={"type": "function", "function": {"name": "get_courses"}},
        tool_choice=LLM_TOOL_CHOICE,
        tools=[stackademy_app.tool_factory_get_courses()],
    )
    logger.debug("Initial response: %s", dump_json_colored(response.model_dump(), "green"))

    message = response.choices[0].message
    while message.tool_calls:
        if message.content and "Goodbye!" in message.content:
            break
        functions_called = process_tool_calls(message)

        response = handle_completion(
            tools=[stackademy_app.tool_factory_get_courses(), stackademy_app.tool_factory_register()],
            tool_choice=ToolChoice.AUTO,
        )
        message = response.choices[0].message
        logger.debug("Updated response: %s", dump_json_colored(response.model_dump(), "green"))

    return response, functions_called
