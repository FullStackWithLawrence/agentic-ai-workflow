# -*- coding: utf-8 -*-
"""
Prompt engineering and management for Stackademy.
Handles function calling and response parsing.
"""

import json
from typing import Union

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
from app.logging_config import get_logger, setup_logging
from app.stackademy import stackademy_app


# Initialize logging
setup_logging()
logger = get_logger(__name__)


messages: list[
    Union[
        ChatCompletionSystemMessageParam,
        ChatCompletionUserMessageParam,
        ChatCompletionAssistantMessageParam,
        ChatCompletionToolMessageParam,
    ]
] = [
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
    ),
    ChatCompletionAssistantMessageParam(
        role="assistant",
        content="How can I assist you with Stackademy today?",
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
        course_code = arguments.get("course_code", "MISSING COURSE CODE")
        email = arguments.get("email", "MISSING EMAIL")
        full_name = arguments.get("full_name", "MISSING NAME")

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
                    role="assistant", content=assistant_content, tool_calls=tool_calls_param
                )
            )
            logger.info("Function call detected: %s with args %s", function_name, function_args)

            function_result = handle_function_call(function_name, function_args)

            tool_message = ChatCompletionToolMessageParam(
                role="tool", content=function_result, tool_call_id=tool_call.id
            )
            messages.append(tool_message)

        logger.debug(
            "Updated messages: %s", [msg.model_dump() if not isinstance(msg, dict) else msg for msg in messages]
        )
    return functions_called


# pylint: disable=too-many-locals
def completion(prompt: str) -> tuple[ChatCompletion, list[str]]:
    """LLM text completion"""

    openai.api_key = settings.OPENAI_API_KEY
    model = settings.OPENAI_API_MODEL
    temperature = settings.OPENAI_API_TEMPERATURE
    max_tokens = settings.OPENAI_API_MAX_TOKENS
    messages.append(ChatCompletionUserMessageParam(role="user", content=prompt))
    functions_called = []

    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        tool_choice={"type": "function", "function": {"name": "get_courses"}},
        tools=[stackademy_app.tool_factory_get_courses()],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    logger.debug("Initial response: %s", response.model_dump())

    message = response.choices[0].message
    while message.tool_calls:
        functions_called = process_tool_calls(message)

        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            tools=[stackademy_app.tool_factory_get_courses(), stackademy_app.tool_factory_register()],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        message = response.choices[0].message
        logger.debug("Updated response: %s", response.model_dump())

    return response, functions_called
