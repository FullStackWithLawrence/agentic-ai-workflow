# -*- coding: utf-8 -*-
"""
Utility functions for Stackademy.
"""

import json


def dump_json_colored(data, color="reset", indent=2, sort_keys=False):
    """
    Dumps a JSON dictionary with colored text output.

    Args:
        data: Dictionary or JSON-serializable object to dump
        color: Color for the text output ("blue" or "green")
        indent: Number of spaces for JSON indentation (default: 2)
        sort_keys: Whether to sort dictionary keys (default: True)

    Returns:
        str: Colored JSON string

    Raises:
        ValueError: If color is not "blue" or "green"
        TypeError: If data is not JSON serializable
    """
    # ANSI color codes
    colors = {
        "blue": "\033[94m",  # Bright blue
        "green": "\033[92m",  # Bright green
        "reset": "\033[0m",  # Reset to default color
    }

    if color not in ["blue", "green"]:
        raise ValueError("Color must be either 'blue' or 'green'")

    try:
        json_str = json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
        colored_json = f"{colors[color]}{json_str}{colors['reset']}"
        return colored_json
    except (TypeError, ValueError) as e:
        raise TypeError(f"Data is not JSON serializable: {e}") from e
