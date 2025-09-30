# -*- coding: utf-8 -*-
"""Stackademy application with MySQL database integration."""

from enum import Enum
from typing import Any, Dict, List, Optional

from openai.types.chat import ChatCompletionFunctionToolParam
from pydantic import BaseModel, Field

from app.database import db
from app.exceptions import ConfigurationException
from app.logging_config import get_logger, setup_logging


setup_logging()
logger = get_logger(__name__)


class StackademySpecializationArea(str, Enum):
    """Available specialization areas for courses."""

    AI = "AI"
    MOBILE = "mobile"
    WEB = "web"
    DATABASE = "database"
    NETWORK = "network"
    NEURAL_NETWORKS = "neural networks"


class StackademyGetCoursesParams(BaseModel):
    """Parameters for the get_courses function."""

    max_cost: Optional[float] = Field(
        None, description="The maximum cost that a student is willing to pay for a course."
    )
    description: Optional[StackademySpecializationArea] = Field(
        None, description="Areas of specialization for courses in the catalogue."
    )


class StackademyRegisterCourseParams(BaseModel):
    """Parameters for the register_course function."""

    course_code: str = Field(description="The unique code for the course.")
    email: str = Field(description="The email address of the new user.")
    full_name: str = Field(description="The full name of the new user.")


class Stackademy:
    """Main application class for Stackademy with database functionality."""

    def __init__(self):
        """Initialize the Stackademy application."""
        self.db = db

    def _log_success(self, message: str) -> None:
        """
        Log a success message with colorized console output.

        Args:
            message: The success message to log
        """
        print(f"\033[1;92m{message}\033[0m")
        logger.info(message)

    def tool_factory_get_courses(self) -> ChatCompletionFunctionToolParam:
        """LLM Factory function to create a tool for getting courses"""
        return ChatCompletionFunctionToolParam(
            type="function",
            function={
                "name": "get_courses",
                "description": "returns up to 10 rows of course detail data, filtered by the maximum cost a student is willing to pay for a course and the area of specialization.",
                "parameters": StackademyGetCoursesParams.model_json_schema(),
            },
        )

    def tool_factory_register(self) -> ChatCompletionFunctionToolParam:
        """LLMFactory function to create a tool for registering a user"""
        return ChatCompletionFunctionToolParam(
            type="function",
            function={
                "name": "register_course",
                "description": "Register a student in a course with the provided details.",
                "parameters": StackademyRegisterCourseParams.model_json_schema(),
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

    def verify_course(self, course_code: str) -> bool:
        """
        Verify if a course exists in the database.
        Args:
            course_code (str): The course code to verify
        Returns:
            bool: True if the course exists, False otherwise
        """
        query = "SELECT * FROM courses WHERE course_code = %s"
        try:
            result = self.db.execute_query(query, (course_code,))
            retval = len(result) > 0
            if retval:
                logger.info("verified course_code: %s", course_code)
            else:
                logger.warning("course_code not found: %s", course_code)
            return retval
        # pylint: disable=broad-except
        except Exception as e:
            logger.error("Failed to retrieve courses: %s", e)
            return False

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
        if not self.verify_course(course_code):
            logger.error("Course code %s does not exist.", course_code)
            return False

        success_message = f"Successfully registered {full_name} ({email}) for course {course_code}."
        self._log_success(success_message)
        return True


stackademy_app = Stackademy()
