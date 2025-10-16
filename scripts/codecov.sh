#!/bin/bash

# Always resolve the path to coverage.xml relative to the repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
COVERAGE_FILE="$REPO_ROOT/coverage.xml"
BRANCH="main"
CODECOV_TOKEN="${CODECOV_TOKEN}"

if [[ -z "$CODECOV_TOKEN" ]]; then
  echo "Error: CODECOV_TOKEN environment variable not set."
  exit 1
fi

if [[ ! -f "$COVERAGE_FILE" ]]; then
  echo "Error: $COVERAGE_FILE not found."
  exit 1
fi

COMMIT_SHA=$(git -C "$REPO_ROOT" rev-parse origin/main)

curl -X POST -F "file=@${COVERAGE_FILE}" \
  "https://codecov.io/upload/v4?token=${CODECOV_TOKEN}&branch=${BRANCH}&commit=${COMMIT_SHA}"
