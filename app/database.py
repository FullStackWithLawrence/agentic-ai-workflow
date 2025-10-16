# -*- coding: utf-8 -*-
"""Database connection and utilities for MySQL."""

from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

import pymysql

from app.exceptions import ConfigurationException
from app.logging_config import get_logger, setup_logging
from app.settings import (
    MYSQL_CHARSET,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)


setup_logging()
logger = get_logger(__name__)


class DatabaseConnection:
    """MySQL database connection manager."""

    def __init__(self):
        """Initialize database connection parameters."""
        self.host = MYSQL_HOST
        self.port = MYSQL_PORT
        self.user = MYSQL_USER
        self.password = MYSQL_PASSWORD
        self.database = MYSQL_DATABASE
        self.charset = MYSQL_CHARSET

        # Validate required configuration
        if not all([self.host, self.user, self.password, self.database]):
            raise ConfigurationException(
                "Missing required MySQL configuration. Please check your environment variables: "
                "MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE"
            )

    @property
    def connection_string(self) -> str:
        """Return the database connection string."""
        return f"{self.user}@{self.host}:{self.port}/{self.database}"

    def get_connection(self) -> pymysql.Connection:
        """
        Create and return a new MySQL connection.

        Returns:
            pymysql.Connection: Active database connection

        Raises:
            pymysql.Error: If connection fails
        """
        logger.debug("Connecting to MySQL database at %s:%s", self.host, self.port)
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
            )
            return connection
        except pymysql.Error as e:
            raise pymysql.Error(f"Failed to connect to MySQL database: {e}")

    @contextmanager
    def get_cursor(self) -> Iterator[pymysql.cursors.DictCursor]:
        """
        Context manager for database operations with automatic connection handling.

        Yields:
            pymysql.cursors.DictCursor: Database cursor for executing queries

        Usage:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM courses")
                results = cursor.fetchall()
        """
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            yield cursor
            connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if connection:
                connection.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results.

        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query

        Returns:
            List[Dict[str, Any]]: Query results as list of dictionaries
        """
        logger.debug("Executing query: %s with params: %s", query, params)
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return list(cursor.fetchall())

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.

        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query

        Returns:
            int: Number of affected rows
        """
        logger.debug("Executing update: %s with params: %s", query, params)
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount

    def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        # pylint: disable=broad-except
        except Exception as e:
            logger.error("Database connection test failed: %s", e)
            return False


# Global database instance
db = DatabaseConnection()
