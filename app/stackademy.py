# -*- coding: utf-8 -*-
"""Stackademy application with MySQL database integration."""

from typing import Any, Dict, List, Optional

from openai.types.chat import ChatCompletionFunctionToolParam

from app.database import db
from app.exceptions import ConfigurationException
from app.function_schemas import GetCoursesParams, RegisterCourseParams
from app.logging_config import get_logger, setup_logging


# Initialize logging
setup_logging()
logger = get_logger(__name__)


class StackademyApp:
    """Main application class for Stackademy with database functionality."""

    def __init__(self):
        """Initialize the Stackademy application."""
        self.db = db

    def tool_factory_get_courses(self) -> ChatCompletionFunctionToolParam:
        """LLM Factory function to create a tool for getting courses"""
        return ChatCompletionFunctionToolParam(
            type="function",
            function={
                "name": "get_courses",
                "description": "returns up to 10 rows of course detail data, filtered by the maximum cost a student is willing to pay for a course and the area of specialization.",
                "parameters": GetCoursesParams.model_json_schema(),
            },
        )

    def tool_factory_register(self) -> ChatCompletionFunctionToolParam:
        """LLMFactory function to create a tool for registering a user"""
        return ChatCompletionFunctionToolParam(
            type="function",
            function={
                "name": "register_course",
                "description": "Register a student in a course with the provided details.",
                "parameters": RegisterCourseParams.model_json_schema(),
            },
        )

    def test_database_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            return self.db.test_connection()
        # pylint: disable=broad-except
        except Exception as e:
            logger.error("Database connection test failed: %s", e)
            return False

    def get_courses(self, description: Optional[str] = None, max_cost: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Retrieve a list of courses from the database.

        Args:
            description (str, optional): Filter courses by description content
            max_cost (float, optional): Filter courses by maximum cost

        Returns:
            List[Dict[str, Any]]: List of courses matching the criteria
        """
        # Base query
        query = """
        SELECT
            c.course_code,
            c.course_name,
            c.description,
            c.cost,
            prerequisite.course_code AS prerequisite_course_code,
            prerequisite.course_name AS prerequisite_course_name
        FROM courses c
        LEFT JOIN courses prerequisite ON c.prerequisite_id = prerequisite.course_id
        """

        # Build WHERE clause dynamically
        where_conditions = []
        params = []

        if description is not None:
            where_conditions.append("c.description LIKE %s")
            params.append(f"%{description}%")

        if max_cost is not None:
            where_conditions.append("c.cost <= %s")
            params.append(max_cost)

        # Add WHERE clause if we have conditions
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)

        query += " ORDER BY c.prerequisite_id"
        logger.info("get_courses() executing db query with params: %s", params)
        try:
            return self.db.execute_query(query, tuple(params))
        # pylint: disable=broad-except
        except Exception as e:
            logger.error("Failed to retrieve courses: %s", e)
            return []

    def register_course(self, course_code: str, email: str, full_name: str) -> bool:
        """
        Register a user for a course.

        Args:
            course_code (str): The course code to register for

            email (str): The user's email address
            full_name (str): The user's full name
        Returns:
            bool: True if registration is successful, False otherwise
        """
        logger.info("Registering %s (%s) for course %s...", full_name, email, course_code)
        return True


def main():
    """Main function to demonstrate database functionality."""
    print("Stackademy MySQL Database Demo")
    print("=" * 50)

    try:
        # Initialize the application
        app = StackademyApp()

        # Test database connection
        logger.info("Testing database connection...")
        if not app.test_database_connection():
            logger.error("Database connection failed. Please check your configuration.")
            return
        logger.info("✅ Database connection successful!")

        # Get courses
        logger.info("Retrieving courses...")
        courses = app.get_courses(description="python")
        for course in courses:
            logger.info(
                "  - %s (%s) - %s - $%s",
                course["course_name"],
                course["course_code"],
                course["description"],
                course["cost"],
            )

    except ConfigurationException as e:
        logger.error("Configuration error: %s", e)
    # pylint: disable=broad-except
    except Exception as e:
        logger.error("Application error: %s", e)


stackademy_app = StackademyApp()

if __name__ == "__main__":
    main()
