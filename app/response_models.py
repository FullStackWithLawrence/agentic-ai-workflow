# -*- coding: utf-8 -*-
"""Response models for structured outputs from OpenAI."""

from typing import List, Optional

from pydantic import BaseModel, Field


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
