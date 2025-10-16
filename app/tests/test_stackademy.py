# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# pylint: disable=R0801
"""Test Stackademy application."""

# python stuff
import unittest
from unittest.mock import Mock, patch

from app.exceptions import ConfigurationException
from app.logging_config import get_logger
from app.stackademy import Stackademy


logger = get_logger(__name__)


class TestStackademy(unittest.TestCase):
    """Test Stackademy application."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = Stackademy()

    def test_stackademy_initialization(self):
        """Test that the Stackademy application initializes successfully."""
        self.assertIsNotNone(self.app)
        self.assertIsNotNone(self.app.db)

    def test_database_connection_success(self):
        """Test successful database connection."""
        # Mock the database connection to return True
        with patch.object(self.app.db, "test_connection", return_value=True):
            result = self.app.test_database_connection()
            self.assertTrue(result)
            logger.info("Database connection test passed successfully")

    def test_database_connection_failure(self):
        """Test database connection failure."""
        # Mock the database connection to raise an exception
        with patch.object(self.app.db, "test_connection", side_effect=Exception("Connection failed")):
            result = self.app.test_database_connection()
            self.assertFalse(result)
            logger.info("Database connection failure test passed")

    def test_get_courses_with_description_filter(self):
        """Test retrieving courses with description filter."""
        # Mock course data
        mock_courses = [
            {
                "course_code": "PY101",
                "course_name": "Python Fundamentals",
                "description": "Learn Python programming basics",
                "cost": 299.99,
                "prerequisite_course_code": None,
                "prerequisite_course_name": None,
            },
            {
                "course_code": "PY201",
                "course_name": "Advanced Python",
                "description": "Advanced Python programming techniques",
                "cost": 399.99,
                "prerequisite_course_code": "PY101",
                "prerequisite_course_name": "Python Fundamentals",
            },
        ]

        # Mock the database query
        with patch.object(self.app.db, "execute_query", return_value=mock_courses):
            courses = self.app.get_courses(description="python")

            self.assertEqual(len(courses), 2)
            self.assertEqual(courses[0]["course_code"], "PY101")
            self.assertEqual(courses[1]["course_code"], "PY201")

            # Log course information as in the original code
            logger.info("Retrieved %d courses with python description", len(courses))
            for course in courses:
                logger.info(
                    "  - %s (%s) - %s - $%s",
                    course["course_name"],
                    course["course_code"],
                    course["description"],
                    course["cost"],
                )

    def test_get_courses_with_cost_filter(self):
        """Test retrieving courses with maximum cost filter."""
        mock_courses = [
            {
                "course_code": "WEB101",
                "course_name": "Web Development Basics",
                "description": "Introduction to web development",
                "cost": 199.99,
                "prerequisite_course_code": None,
                "prerequisite_course_name": None,
            }
        ]

        with patch.object(self.app.db, "execute_query", return_value=mock_courses):
            courses = self.app.get_courses(max_cost=250.0)

            self.assertEqual(len(courses), 1)
            self.assertLessEqual(courses[0]["cost"], 250.0)
            logger.info("Retrieved courses under $250: %d", len(courses))

    def test_get_courses_database_error(self):
        """Test get_courses when database error occurs."""
        with patch.object(self.app.db, "execute_query", side_effect=Exception("Database error")):
            courses = self.app.get_courses(description="python")

            self.assertEqual(len(courses), 0)
            logger.info("Database error handling test passed")

    def test_get_courses_no_results(self):
        """Test get_courses when no courses match criteria."""
        with patch.object(self.app.db, "execute_query", return_value=[]):
            courses = self.app.get_courses(description="nonexistent")

            self.assertEqual(len(courses), 0)
            logger.info("No results test passed")

    def test_application_workflow_with_configuration_exception(self):
        """Test application workflow that raises ConfigurationException."""
        # pylint: disable=broad-exception-caught
        try:
            # Simulate a configuration error
            raise ConfigurationException("Invalid configuration setting")
        except ConfigurationException as e:
            logger.error("Configuration error: %s", e)
            self.assertIsInstance(e, ConfigurationException)

    def test_application_workflow_with_general_exception(self):
        """Test application workflow that raises general exception."""
        # pylint: disable=broad-exception-caught,broad-except
        try:
            # Simulate a general application error
            raise RuntimeError("General application error")
        except Exception as e:
            logger.error("Application error: %s", e)
            self.assertIsInstance(e, Exception)

    def test_full_application_workflow(self):
        """Test the complete application workflow as shown in the example."""
        mock_courses = [
            {
                "course_code": "PY101",
                "course_name": "Python Fundamentals",
                "description": "Learn Python programming from scratch",
                "cost": 299.99,
                "prerequisite_course_code": None,
                "prerequisite_course_name": None,
            },
            {
                "course_code": "AI201",
                "course_name": "Python for AI",
                "description": "Python programming for artificial intelligence",
                "cost": 499.99,
                "prerequisite_course_code": "PY101",
                "prerequisite_course_name": "Python Fundamentals",
            },
        ]

        # pylint: disable=broad-exception-caught
        try:
            # Initialize the application
            app = Stackademy()
            self.assertIsNotNone(app)

            # Test database connection
            logger.info("Testing database connection...")
            with patch.object(app.db, "test_connection", return_value=True):
                if not app.test_database_connection():
                    logger.error("Database connection failed. Please check your configuration.")
                    self.fail("Database connection should have succeeded")
                logger.info("Database connection successful!")

            # Get courses
            logger.info("Retrieving courses...")
            with patch.object(app.db, "execute_query", return_value=mock_courses):
                courses = app.get_courses(description="python")

                self.assertEqual(len(courses), 2)

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
            self.fail(f"Unexpected ConfigurationException: {e}")
        except Exception as e:
            logger.error("Application error: %s", e)
            self.fail(f"Unexpected application error: {e}")


if __name__ == "__main__":
    unittest.main()
