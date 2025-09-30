# -*- coding: utf-8 -*-
"""Stackademy application with MySQL database integration."""

from typing import Any, Dict, List, Optional

from app.database import db
from app.exceptions import ConfigurationException


class StackademyApp:
    """Main application class for Stackademy with database functionality."""

    def __init__(self):
        """Initialize the Stackademy application."""
        self.db = db

    def test_database_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            return self.db.test_connection()
        # pylint: disable=broad-except
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False

    def get_courses(self, description: Optional[str] = None, max_cost: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Retrieve a list of courses from the database.

        Args:
            description (str, optional): Filter courses by description content
            max_cost (float, optional): Filter courses by maximum cost

        Returns:
            List[Dict[str, Any]]: List of courses matching the criteria
        """
        # Base query
        query = """
        SELECT
            c.course_code,
            c.course_name,
            c.description,
            c.cost,
            prerequisite.course_code AS prerequisite_course_code,
            prerequisite.course_name AS prerequisite_course_name
        FROM courses c
        LEFT JOIN courses prerequisite ON c.prerequisite_id = prerequisite.course_id
        """

        # Build WHERE clause dynamically
        where_conditions = []
        params = []

        if description is not None:
            where_conditions.append("c.description LIKE %s")
            params.append(f"%{description}%")

        if max_cost is not None:
            where_conditions.append("c.cost <= %s")
            params.append(max_cost)

        # Add WHERE clause if we have conditions
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)

        query += " ORDER BY c.prerequisite_id"

        try:
            return self.db.execute_query(query, tuple(params))
        # pylint: disable=broad-except
        except Exception as e:
            print(f"Failed to retrieve courses: {e}")
            return []


def main():
    """Main function to demonstrate database functionality."""
    print("Stackademy MySQL Database Demo")
    print("=" * 50)

    try:
        # Initialize the application
        app = StackademyApp()

        # Test database connection
        print("Testing database connection...")
        if not app.test_database_connection():
            print("Database connection failed. Please check your configuration.")
            return
        print("✅ Database connection successful!")

        # Get courses
        print("\nRetrieving courses...")
        courses = app.get_courses(description="python")
        for course in courses:
            print(
                f"  - {course['course_name']} ({course['course_code']}) - {course['description']} - ${course['cost']}"
            )

    except ConfigurationException as e:
        print(f"Configuration error: {e}")
    # pylint: disable=broad-except
    except Exception as e:
        print(f"Application error: {e}")


stackademy_app = StackademyApp()

if __name__ == "__main__":
    main()
