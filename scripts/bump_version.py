"""
Script to update the semantic version in pyproject.toml and Dockerfile.

Called automatically from semantic-release hooks.
see: release.config.js in the root directory.

Usage:
    python scripts/bump_version.py <new_version>

Updates:
- app/__version__.py
- pyproject.toml
- Dockerfile
"""

import re
import sys
from pathlib import Path


def update_version_in_file(filepath, pattern, replacement):
    """Update the version in the specified file."""
    path = Path(filepath)
    text = path.read_text(encoding="utf-8")
    new_text = re.sub(pattern, replacement, text)
    path.write_text(new_text, encoding="utf-8")


def main():
    """Main function to update version in multiple files."""
    if len(sys.argv) != 2:
        print("Usage: python bump_version.py <new_version>")
        sys.exit(1)
    new_version = sys.argv[1]

    # Validate semantic version: ##.##.##, with a prerelease suffix on alpha and beta (0.2.0-alpha.1)
    if not re.match(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?$", new_version):
        print("Error: Version must be ##.##.## or ##.##.##-<prerelease> (e.g., 0.1.20, 0.2.0-alpha.1)")
        sys.exit(1)

    # Update __version__.py
    update_version_in_file("app/__version__.py", r'__version__\s*=\s*["\'].*?["\']', f'__version__ = "{new_version}"')

    # Update pyproject.toml: only the [project] version line, not target-version
    update_version_in_file("pyproject.toml", r'(?m)^version\s*=\s*["\'].*?["\']', f'version = "{new_version}"')

    # Update Dockerfile (example: ARG VERSION=...)
    update_version_in_file(
        "Dockerfile",
        r'org\.opencontainers\.image\.version="[^"]+"',
        f'org.opencontainers.image.version="{new_version}"',
    )

    print(f"Version updated to {new_version} in app/__version__.py, pyproject.toml and Dockerfile")


if __name__ == "__main__":
    main()
