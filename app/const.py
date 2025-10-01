# -*- coding: utf-8 -*-
"""Constants for the Stackademy application."""

MISSING = "MISSING"


class ToolChoice:
    """Enumeration for tool choice strategies."""

    AUTO = "auto"
    REQUIRED = "required"
    NONE = "none"
    GET_COURSES = {"type": "function", "function": {"name": "get_courses"}}
