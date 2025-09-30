# -*- coding: utf-8 -*-
"""Pydantic models for OpenAI function calling schemas."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SpecializationArea(str, Enum):
    """Available specialization areas for courses."""

    AI = "AI"
    MOBILE = "mobile"
    WEB = "web"
    DATABASE = "database"
    NETWORK = "network"
    NEURAL_NETWORKS = "neural networks"


class GetCoursesParams(BaseModel):
    """Parameters for the get_courses function."""

    max_cost: Optional[float] = Field(
        None, description="The maximum cost that a student is willing to pay for a course."
    )
    description: Optional[SpecializationArea] = Field(
        None, description="Areas of specialization for courses in the catalogue."
    )


class RegisterCourseParams(BaseModel):
    """Parameters for the register_course function."""

    course_code: str = Field(description="The unique code for the course.")
    email: str = Field(description="The email address of the new user.")
    full_name: str = Field(description="The full name of the new user.")
