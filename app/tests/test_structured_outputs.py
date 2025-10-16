# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# pylint: disable=R0801,W0613,W0718
"""Test structured outputs."""

# python stuff
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import PropertyMock, patch

import app.structured_outputs as so


HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = str(Path(HERE).parent.parent)
PYTHON_ROOT = str(Path(PROJECT_ROOT).parent)
if PYTHON_ROOT not in sys.path:
    sys.path.append(PYTHON_ROOT)  # noqa: E402


class TestStructuredOutputs(unittest.TestCase):
    """Test structured outputs."""

    def test_course_model(self):
        """Test that the Course model is created correctly."""
        course = so.Course(
            course_code="CS101",
            course_name="Intro to CS",
            description="Basics",
            cost=100.0,
        )
        self.assertEqual(course.course_code, "CS101")
        self.assertEqual(course.cost, 100.0)

    def test_course_search_response_model(self):
        """Test that the CourseSearchResponse model is created correctly."""
        course = so.Course(
            course_code="CS101",
            course_name="Intro to CS",
            description="Basics",
            cost=100.0,
        )
        resp = so.CourseSearchResponse(courses=[course], total_count=1)
        self.assertEqual(resp.total_count, 1)
        self.assertEqual(len(resp.courses), 1)

    def test_registration_response_model(self):
        """Test that the RegistrationResponse model is created correctly."""
        resp = so.RegistrationResponse(success=True, message="OK", registration_id="REG-CS101-0001")
        self.assertTrue(resp.success)
        self.assertEqual(resp.registration_id, "REG-CS101-0001")

    @patch(
        "app.structured_outputs.stackademy_app.get_courses",
        return_value=[{"course_code": "CS101", "course_name": "Intro to CS", "description": "Basics", "cost": 100.0}],
    )
    @patch("app.structured_outputs.StackademyGetCoursesParams", autospec=True)
    def test_get_courses_with_structured_output(self, mock_params, mock_get_courses):
        """Test that get_courses_with_structured_output works correctly."""
        mock_params.return_value.description = None
        mock_params.return_value.max_cost = None
        resp = so.get_courses_with_structured_output(description="CS", max_cost=200.0)
        self.assertIsInstance(resp, so.CourseSearchResponse)
        self.assertGreaterEqual(resp.total_count, 1)

    @patch("app.structured_outputs.stackademy_app.register_course", return_value=True)
    @patch("app.structured_outputs.StackademyRegisterCourseParams", autospec=True)
    def test_register_course_with_structured_output(self, mock_params, mock_register):
        """Test that register_course_with_structured_output works correctly."""
        mock_params.return_value.course_code = "CS101"
        mock_params.return_value.email = "a@b.com"
        mock_params.return_value.full_name = "Test User"
        resp = so.register_course_with_structured_output("CS101", "a@b.com", "Test User")
        self.assertTrue(resp.success)
        self.assertIn("Successfully registered", resp.message)

    def test_completion_with_structured_output(self):
        """Test that completion_with_structured_output does not raise exceptions."""
        try:
            so.completion_with_structured_output("prompt", so.CourseSearchResponse)
        except Exception as e:
            self.fail(f"completion_with_structured_output raised an exception: {e}")

    @patch("app.structured_outputs.StackademyGetCoursesParams", side_effect=Exception("fail"))
    def test_get_courses_with_structured_output_exception(self, mock_params):
        """Test that get_courses_with_structured_output handles exceptions."""
        resp = so.get_courses_with_structured_output(description="CS", max_cost=200.0)
        self.assertIsInstance(resp, so.CourseSearchResponse)
        self.assertEqual(resp.total_count, 0)
        self.assertEqual(resp.courses, [])

    @patch("app.structured_outputs.StackademyGetCoursesParams", side_effect=Exception("validation error"))
    def test_get_courses_with_structured_output_validation_error(self, mock_params):
        """Test that get_courses_with_structured_output handles validation errors."""
        resp = so.get_courses_with_structured_output(description="CS", max_cost=200.0)
        self.assertIsInstance(resp, so.CourseSearchResponse)
        self.assertEqual(resp.total_count, 0)
        self.assertEqual(resp.courses, [])

    @patch("app.structured_outputs.StackademyRegisterCourseParams", side_effect=Exception("validation error"))
    def test_register_course_with_structured_output_validation_error(self, mock_params):
        """Test that register_course_with_structured_output handles validation errors."""
        resp = so.register_course_with_structured_output("CS101", "a@b.com", "Test User")
        self.assertFalse(resp.success)

        # pylint: disable=E1101
        self.assertIn("unexpected error", resp.message.lower())

    @patch("app.structured_outputs.StackademyRegisterCourseParams", side_effect=Exception("fail"))
    def test_register_course_with_structured_output_exception(self, mock_params):
        """Test that register_course_with_structured_output handles exceptions."""
        resp = so.register_course_with_structured_output("CS101", "a@b.com", "Test User")
        self.assertFalse(resp.success)
        # pylint: disable=E1101
        self.assertIn("unexpected error", resp.message.lower())

    def test_completion_with_structured_output_exception(self):
        """Test that completion_with_structured_output handles exceptions."""
        with patch("app.structured_outputs.settings.OPENAI_API_KEY", new_callable=PropertyMock) as mock_key:
            mock_key.side_effect = Exception("fail")
            self.assertIsNone(so.completion_with_structured_output("prompt", so.CourseSearchResponse))

    @patch("app.structured_outputs.StackademyGetCoursesParams", autospec=True)
    @patch("app.structured_outputs.stackademy_app.get_courses", return_value=[])
    def test_get_courses_with_structured_output_no_courses(self, mock_get_courses, mock_params):
        """Test that get_courses_with_structured_output handles no courses found."""

        mock_params.return_value.description = None
        mock_params.return_value.max_cost = None
        resp = so.get_courses_with_structured_output(description="nonexistent", max_cost=200.0)
        self.assertIsInstance(resp, so.CourseSearchResponse)
        self.assertEqual(resp.total_count, 0)
        self.assertEqual(resp.courses, [])

    @patch("app.structured_outputs.StackademyRegisterCourseParams", autospec=True)
    @patch("app.structured_outputs.stackademy_app.register_course", return_value=False)
    def test_register_course_with_structured_output_failure(self, mock_register, mock_params):
        """Test that register_course_with_structured_output handles registration failure."""

        mock_params.return_value.course_code = "CS101"
        mock_params.return_value.email = "a@b.com"
        mock_params.return_value.full_name = "Test User"
        resp = so.register_course_with_structured_output("CS101", "a@b.com", "Test User")
        self.assertFalse(resp.success)
        self.assertIn("Registration failed", resp.message)

    def test_completion_with_structured_output_beta(self):
        """Test that completion_with_structured_output handles beta feature stub."""

        self.assertIsNone(so.completion_with_structured_output("prompt", so.CourseSearchResponse))
