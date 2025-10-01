# -*- coding: utf-8 -*-
"""Settings for the app."""

import logging
import os

from dotenv import load_dotenv

from app.const import ToolChoice
from app.exceptions import ConfigurationException


load_dotenv()
SET_ME_PLEASE = "SET-ME-PLEASE"

# General settings
LOGGING_LEVEL = int(os.getenv("LOGGING_LEVEL", str(logging.INFO)))
TOOL_CHOICE = os.getenv("TOOL_CHOICE", ToolChoice.REQUIRED)


# OpenAI API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", SET_ME_PLEASE)
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-4o-mini")
OPENAI_API_TEMPERATURE = float(os.getenv("OPENAI_API_TEMPERATURE", "0.0"))
OPENAI_API_MAX_TOKENS = int(os.getenv("OPENAI_API_MAX_TOKENS", "4096"))


# MySQL database settings
MYSQL_HOST = os.getenv("MYSQL_HOST", SET_ME_PLEASE)
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", SET_ME_PLEASE)
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", SET_ME_PLEASE)
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", SET_ME_PLEASE)
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")

# application configuration validations
if SET_ME_PLEASE in (
    MYSQL_HOST,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DATABASE,
):
    raise ConfigurationException("MySQL configuration is incomplete. Please check your .env file.")

if OPENAI_API_KEY in (None, SET_ME_PLEASE):
    raise ConfigurationException("No OpenAI API key found. Please add it to your .env file.")
