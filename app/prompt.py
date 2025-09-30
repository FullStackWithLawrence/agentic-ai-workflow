# -*- coding: utf-8 -*-
"""
Prompt engineering and management for Stackademy.
Handles function calling and response parsing.
"""

import json
import random
from typing import Optional, Union

import openai
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionToolParam,
    ChatCompletionMessage,
    ChatCompletionMessageFunctionToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

from app import settings
from app.stackademy import stackademy_app


def tool_factory_get_courses() -> ChatCompletionFunctionToolParam:
    """Factory function to create a tool for getting courses"""
    return ChatCompletionFunctionToolParam(
        type="function",
        function={
            "name": "get_courses",
            "description": "returns up to 10 rows of course detail data, filtered by the maximum cost a student is willing to pay for a course and the area of specialization.\n",
            "parameters": {
                "type": "object",
                "required": [],
                "properties": {
                    "max_cost": {
                        "type": "number",
                        "description": "the maximum cost that a student is willing to pay for a course.",
                    },
                    "description": {
                        "enum": ["AI", "mobile", "web", "database", "network", "neural networks"],
                        "type": "string",
                        "description": "areas of specialization for courses in the catalogue.",
                    },
                },
                "additionalProperties": False,
            },
        },
    )


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
            Prioritize use of the functions available to you as needed.
            Do not provide answers that are not based on the functions available to you.
            Your task is to assist users with their queries related to the platform,
            including course information, enrollment procedures, and general support.
            You should respond in a concise and clear manner, providing accurate information based on the user's request.
            """,
    ),
    ChatCompletionAssistantMessageParam(
        role="assistant",
        content="How can I assist you with Stackademy today?",
    ),
]

# Define tools separately
tools = [tool_factory_get_courses()]


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

    return json.dumps({"error": f"Unknown function: {function_name}"})


# pylint: disable=too-many-locals
def completion(prompt: str):
    """LLM text completion"""

    # Set the OpenAI API key
    # -------------------------------------------------------------------------
    openai.api_key = settings.OPENAI_API_KEY

    # setup our text completion prompt
    # -------------------------------------------------------------------------
    model = settings.OPENAI_API_MODEL
    temperature = settings.OPENAI_API_TEMPERATURE
    max_tokens = settings.OPENAI_API_MAX_TOKENS
    messages.append(ChatCompletionUserMessageParam(role="user", content=prompt))

    # Call the OpenAI API
    # -------------------------------------------------------------------------
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        tool_choice={"type": "function", "function": {"name": "get_courses"}},
        tools=tools,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    print(response.model_dump())

    # Check if the model wants to call a function
    # -------------------------------------------------------------------------
    message = response.choices[0].message

    if message.tool_calls:

        # Process each tool call
        for tool_call in message.tool_calls:

            # For function calls, access via type checking
            if tool_call.type == "function":
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_calls_param = [
                    ChatCompletionMessageFunctionToolCallParam(
                        id=tool_call.id,
                        type="function",
                        function={
                            "name": function_name,
                            "arguments": tool_call.function.arguments,  # Keep as string, don't parse
                        },
                    )
                ]
                assistant_content = message.content if message.content else "Accessing tool..."
                messages.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant", content=assistant_content, tool_calls=tool_calls_param
                    )
                )
                print(f"Function call detected: {function_name} with args {function_args}")

                # Execute the function
                function_result = handle_function_call(function_name, function_args)

                # Add the function result to the conversation
                tool_message = ChatCompletionToolMessageParam(
                    role="tool", content=function_result, tool_call_id=tool_call.id
                )
                messages.append(tool_message)

            print(f"Updated messages: {[msg.model_dump() if not isinstance(msg, dict) else msg for msg in messages]}")

        # Make another API call to get the final response
        final_response = openai.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        final_message = final_response.choices[0].message
        retval = final_message.content
        print(final_response.model_dump())
    else:
        # No function call, just return the content
        retval = message.content

    # Print the response
    # -------------------------------------------------------------------------
    print(retval)
    return retval
