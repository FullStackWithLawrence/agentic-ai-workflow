# -*- coding: utf-8 -*-
"""EXPERIMENTAL: OpenAI's structured outputs with Pydantic models."""

import json
from typing import List, Optional

import openai
from pydantic import BaseModel, Field, ValidationError

from app import settings
from app.logging_config import get_logger
from app.stackademy import (
    StackademyGetCoursesParams,
    StackademyRegisterCourseParams,
    StackademySpecializationArea,
    stackademy_app,
)


class Course(BaseModel):
    """A course in the Stackademy catalog."""

    course_code: str = Field(description="The unique code for the course")
    course_name: str = Field(description="The name of the course")
    description: str = Field(description="Course description")
    cost: float = Field(description="Cost of the course")
    prerequisite_course_code: Optional[str] = Field(description="Prerequisite course code", default=None)
    prerequisite_course_name: Optional[str] = Field(description="Prerequisite course name", default=None)


class CourseSearchResponse(BaseModel):
    """Response model for course search results."""

    courses: List[Course] = Field(description="List of courses matching the search criteria")
    total_count: int = Field(description="Total number of courses found")


class RegistrationResponse(BaseModel):
    """Response model for course registration."""

    success: bool = Field(description="Whether the registration was successful")
    message: str = Field(description="Human-readable message about the registration result")
    registration_id: Optional[str] = Field(description="Unique registration ID if successful", default=None)


logger = get_logger(__name__)


def get_courses_with_structured_output(
    description: Optional[str] = None, max_cost: Optional[float] = None
) -> CourseSearchResponse:
    """
    Get courses using structured output parsing.

    This ensures the response conforms to our expected schema.
    """
    try:
        # Convert string to enum if provided
        specialization_area = None
        if description:

            try:
                specialization_area = StackademySpecializationArea(description)
            except ValueError:
                logger.warning("Invalid specialization area: %s", description)
                specialization_area = None

        # Validate input parameters using Pydantic
        params = StackademyGetCoursesParams(description=specialization_area, max_cost=max_cost)

        # Get raw course data
        courses_data = stackademy_app.get_courses(
            description=params.description if params.description else None, max_cost=params.max_cost
        )

        courses = [Course(**course_dict) for course_dict in courses_data]

        # Create structured response
        return CourseSearchResponse(courses=courses, total_count=len(courses))

    except ValidationError as e:
        logger.error("Parameter validation error: %s", e)
        return CourseSearchResponse(courses=[], total_count=0)
    # pylint: disable=broad-except
    except Exception as e:
        logger.error("Error getting courses: %s", e)
        return CourseSearchResponse(courses=[], total_count=0)


def register_course_with_structured_output(course_code: str, email: str, full_name: str) -> RegistrationResponse:
    """
    Register for a course using structured output.
    """
    try:
        # Validate input parameters
        params = StackademyRegisterCourseParams(course_code=course_code, email=email, full_name=full_name)

        # Attempt registration
        success = stackademy_app.register_course(
            course_code=params.course_code, email=params.email, full_name=params.full_name
        )

        if success:
            return RegistrationResponse(
                success=True,
                message=f"Successfully registered {full_name} for course {course_code}",
                registration_id=f"REG-{course_code}-{hash(email) % 10000:04d}",
            )
        return RegistrationResponse(success=False, message="Registration failed. Please try again later.")

    except ValidationError as e:
        logger.error("Parameter validation error: %s", e)
        return RegistrationResponse(success=False, message=f"Invalid parameters: {e}")
    # pylint: disable=broad-except
    except Exception as e:
        logger.error("Registration error: %s", e)
        return RegistrationResponse(success=False, message="An unexpected error occurred during registration.")


# Example of using OpenAI's beta structured outputs (requires openai>=1.0.0)
# pylint: disable=unused-argument
def completion_with_structured_output(prompt: str, response_model: type) -> None:
    """
    Example of using OpenAI's structured output parsing.

    This is available in the beta API and ensures responses conform to schemas.
    """
    try:
        openai.api_key = settings.OPENAI_API_KEY

        # Note: This is a beta feature and may not be available in all OpenAI versions
        # response = openai.beta.chat.completions.parse(
        #     model=settings.OPENAI_API_MODEL,
        #     messages=[{"role": "user", "content": prompt}],
        #     response_format=response_model,
        # )
        #
        # return response.choices[0].message.parsed

        # For now, we'll return a placeholder since this is beta
        logger.info("Structured output parsing would be used here with model: %s", response_model.__name__)
        return None
    # pylint: disable=broad-except
    except Exception as e:
        logger.error("Structured completion error: %s", e)
        raise e
