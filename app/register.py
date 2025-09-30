# -*- coding: utf-8 -*-
"""
User registration and management for Stackademy.
"""

from .prompt import completion


def main():
    """Main function to demonstrate user registration."""
    print("Stackademy User Registration Demo")
    print("=" * 50)

    user_prompt = input("Enter your question: ")
    completion(prompt=user_prompt)


if __name__ == "__main__":
    main()
