# -*- coding: utf-8 -*-
"""
User registration and management for Stackademy.
"""

from .logging_config import get_logger, setup_logging
from .prompt import completion


# Initialize logging
setup_logging()
logger = get_logger(__name__)


def main():
    """Main function to demonstrate user registration."""
    print("Stackademy User Registration Demo")
    print("=" * 50)

    user_prompt = input("Welcome to Stackademy! How can I assist you today? ")

    response, functions_called = completion(prompt=user_prompt)
    while response.choices[0].message.content != "Goodbye!":
        message = response.choices[0].message
        response_message = message.content or ""
        logger.info("ChatGPT: %s", response_message.strip())

        # Check if there's a follow-up question in the response
        if "QUESTION:" in response_message:
            question_line = [
                line.strip() for line in response_message.split("\n") if line.strip().startswith("QUESTION:")
            ][0]
            followup_question = question_line.replace("QUESTION:", "").strip() + " "
        else:
            followup_question = None

        if "get_courses" in functions_called:
            user_prompt = input(followup_question or "Would you like to register for a course? ")
        elif "register_course" in functions_called:
            user_prompt = input(followup_question or "Can I help you with anything else? ")

        response, functions_called = completion(prompt=user_prompt)


if __name__ == "__main__":
    main()
