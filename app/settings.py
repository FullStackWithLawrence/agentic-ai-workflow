# -*- coding: utf-8 -*-
"""Settings for the app."""

import os

from dotenv import load_dotenv

from app.exceptions import ConfigurationException


# Load environment variables from .env file if available
load_dotenv()

# OpenAI API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
OPENAI_API_MODEL = "gpt-4o-mini"
OPENAI_API_TEMPERATURE = 0.0
OPENAI_API_MAX_TOKENS = 4096


# MySQL database settings
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "stackademy")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")

# application configuration validations
if OPENAI_API_KEY in (None, "SET-ME-PLEASE"):
    raise ConfigurationException("No OpenAI API key found. Please add it to your .env file.")
