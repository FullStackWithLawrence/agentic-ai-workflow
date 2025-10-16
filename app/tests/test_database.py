# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# pylint: disable=R0801,W0613,W0719,W0718
"""Test database connectivity."""

# python stuff
import unittest
from unittest.mock import MagicMock, patch

import pymysql

from app.database import ConfigurationException, DatabaseConnection
from app.logging_config import get_logger


logger = get_logger(__name__)


class TestDatabase(unittest.TestCase):
    """Test database."""

    def test_connection_string(self):
        """Test that the connection string is formed correctly."""
        db = DatabaseConnection()
        conn_str = db.connection_string
        self.assertIn("@", conn_str)
        self.assertIn("/", conn_str)

    @patch("app.database.pymysql.connect")
    def test_get_connection_success(self, mock_connect):
        """Test that a connection is returned on success."""
        db = DatabaseConnection()
        mock_connect.return_value = MagicMock()
        conn = db.get_connection()
        self.assertIsNotNone(conn)
        mock_connect.assert_called_once()

    @patch("app.database.pymysql.connect", side_effect=Exception("fail"))
    def test_get_connection_failure(self, mock_connect):
        """Test that an exception is raised on connection failure."""
        db = DatabaseConnection()
        with self.assertRaises(Exception):
            db.get_connection()

    @patch("app.database.DatabaseConnection.get_connection")
    def test_get_cursor_success(self, mock_get_conn):
        """Test that a cursor is returned on success."""
        db = DatabaseConnection()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        with db.get_cursor() as cursor:
            self.assertEqual(cursor, mock_cursor)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.DatabaseConnection.get_connection")
    def test_get_cursor_exception(self, mock_get_conn):
        """Test that an exception during cursor usage rolls back and closes."""
        db = DatabaseConnection()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        def raise_exc(*args, **kwargs):
            raise Exception("fail")

        mock_cursor.execute.side_effect = raise_exc
        try:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            mock_conn.rollback.assert_called_once()
            mock_conn.close.assert_called_once()

    @patch("app.database.DatabaseConnection.get_cursor")
    def test_execute_query(self, mock_get_cursor):
        """Test that a query returns results."""
        db = DatabaseConnection()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"a": 1}]
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        result = db.execute_query("SELECT * FROM test")
        self.assertEqual(result, [{"a": 1}])

    @patch("app.database.DatabaseConnection.get_cursor")
    def test_execute_update(self, mock_get_cursor):
        """Test that an update returns affected row count."""
        db = DatabaseConnection()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 2
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        result = db.execute_update("UPDATE test SET a=1")
        self.assertEqual(result, 2)

    @patch("app.database.DatabaseConnection.get_cursor")
    def test_test_connection_success(self, mock_get_cursor):
        """Test that the database connection is successful."""
        db = DatabaseConnection()
        mock_cursor = MagicMock()
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.return_value = None
        self.assertTrue(db.test_connection())

    @patch("app.database.DatabaseConnection.get_cursor", side_effect=Exception("fail"))
    def test_test_connection_failure(self, mock_get_cursor):
        """Test that the database connection failure is handled."""
        db = DatabaseConnection()
        self.assertFalse(db.test_connection())

    def test_missing_config_raises(self):
        """Test that missing configuration raises ConfigurationException."""
        with (
            patch("app.database.MYSQL_HOST", ""),
            patch("app.database.MYSQL_USER", ""),
            patch("app.database.MYSQL_PASSWORD", ""),
            patch("app.database.MYSQL_DATABASE", ""),
        ):
            with self.assertRaises(ConfigurationException):
                DatabaseConnection()

    @patch("app.database.pymysql.connect", side_effect=pymysql.Error("connection failed"))
    def test_get_connection_raises(self, mock_connect):
        """Test that a pymysql.Error during connection raises the appropriate exception."""
        db = DatabaseConnection()
        with self.assertRaises(pymysql.Error) as ctx:
            db.get_connection()
        self.assertIn("Failed to connect to MySQL database", str(ctx.exception))
