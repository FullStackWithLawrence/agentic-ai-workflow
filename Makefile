SHELL := /bin/bash
REPO_NAME := agentic-ai-workflow

PYTHON ?= python3.13
VENV := venv
BIN := $(VENV)/bin

# scaffold .env from .env.example on first use. The app and the Docker targets read it.
ifeq ("$(wildcard .env)","")
    $(shell cp .env.example .env)
endif
include .env

.PHONY: all help init check-python python-requirements test coverage run clean \
	lint analyze pre-commit-init pre-commit-run \
	docker-check docker-build docker-push docker-run docker-test docker-prune \
	release-dry-run release

# Default target executed when no arguments are given to make.
all: help

# ---------------------------------------------------------
# Development
# ---------------------------------------------------------
# this repository's own virtual environment, from its own pinned requirements.
init:
	@echo "==============================================================================="
	@echo "Creating $(VENV) from requirements/local.txt, and installing the git hooks ..."
	@echo "==============================================================================="
	make check-python
	rm -rf $(VENV)
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements/local.txt
	make pre-commit-init

# requirements/in/*.in, each starting with -r constraints.in, compile into the pinned requirements/*.txt.
python-requirements:
	@echo "==============================================================================="
	@echo "Compiling and updating Python dependency files using pip-compile ..."
	@echo "==============================================================================="
	$(BIN)/pip install --upgrade "pip-tools>=7.5.0"
	$(BIN)/pip-compile requirements/in/base.in -o requirements/base.txt
	$(BIN)/pip-compile requirements/in/local.in -o requirements/local.txt
	$(BIN)/pip install -r requirements/local.txt

check-python:
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo >&2 "$(PYTHON) is not installed. Aborting."; exit 1; }

test:
	@echo "==============================================================================="
	@echo "Running the unit tests ..."
	@echo "==============================================================================="
	$(BIN)/python -m unittest discover -s app/

coverage:
	@echo "==============================================================================="
	@echo "Running the unit tests with a coverage report ..."
	@echo "==============================================================================="
	$(BIN)/coverage run -m unittest discover -s app/
	$(BIN)/coverage report
	$(BIN)/coverage xml

run:
	$(BIN)/python -m app.agent

clean:
	@echo "==============================================================================="
	@echo "Removing build, test and coverage artifacts ..."
	@echo "==============================================================================="
	rm -rf build dist .pytest_cache .mypy_cache .coverage coverage.xml coverage.out htmlcov node_modules
	find . -name __pycache__ -type d -prune -not -path "./$(VENV)/*" -exec rm -rf {} +

# ---------------------------------------------------------
# Code Management
# ---------------------------------------------------------
lint:
	make pre-commit-run

analyze:
	@echo "==============================================================================="
	@echo "Generating code analysis report using cloc ..."
	@echo "==============================================================================="
	cloc . --exclude-ext=svg,json,zip --vcs=git

pre-commit-init:
	@echo "==============================================================================="
	@echo "Installing and configuring pre-commit ..."
	@echo "==============================================================================="
	$(BIN)/pre-commit install
	$(BIN)/pre-commit autoupdate

pre-commit-run:
	@echo "==============================================================================="
	@echo "Running pre-commit hooks on all files ..."
	@echo "==============================================================================="
	$(BIN)/pre-commit run --all-files

# ---------------------------------------------------------
# Docker
# ---------------------------------------------------------
DOCKER_ENV := -e OPENAI_API_KEY=${OPENAI_API_KEY} \
	-e MYSQL_HOST=${MYSQL_HOST} \
	-e MYSQL_PORT=${MYSQL_PORT} \
	-e MYSQL_USER=${MYSQL_USER} \
	-e MYSQL_PASSWORD=${MYSQL_PASSWORD} \
	-e MYSQL_DATABASE=${MYSQL_DATABASE} \
	-e MYSQL_CHARSET=${MYSQL_CHARSET} \
	-e LOGGING_LEVEL=${LOGGING_LEVEL} \
	-e LLM_TOOL_CHOICE=${LLM_TOOL_CHOICE}

docker-check:
	@docker ps >/dev/null 2>&1 || { echo >&2 "This project requires Docker but it's not running. Aborting."; exit 1; }

docker-build:
	@echo "==============================================================================="
	@echo "Building the Docker image ..."
	@echo "==============================================================================="
	make docker-check
	docker build -t ${DOCKERHUB_USERNAME}/${REPO_NAME} . --build-arg ENVIRONMENT=${ENVIRONMENT}

docker-push:
	@echo "==============================================================================="
	@echo "Pushing the Docker image to DockerHub ..."
	@echo "==============================================================================="
	make docker-check
	docker tag ${DOCKERHUB_USERNAME}/${REPO_NAME} ${DOCKERHUB_USERNAME}/${REPO_NAME}:latest
	echo "${DOCKERHUB_ACCESS_TOKEN}" | docker login --username=${DOCKERHUB_USERNAME} --password-stdin
	docker push ${DOCKERHUB_USERNAME}/${REPO_NAME}:latest

docker-run:
	make docker-check
	docker run -it $(DOCKER_ENV) -e ENVIRONMENT=prod ${DOCKERHUB_USERNAME}/${REPO_NAME}:latest

docker-test:
	make docker-check
	docker run --rm $(DOCKER_ENV) -e ENVIRONMENT=local ${DOCKERHUB_USERNAME}/${REPO_NAME}:latest \
		python -m unittest discover -s app/

docker-prune:
	@echo "==============================================================================="
	@echo "Stopping all containers and removing unused Docker objects ..."
	@echo "==============================================================================="
	make docker-check
	@if [ -n "$$(docker ps -aq)" ]; then \
		docker stop $$(docker ps -aq); \
	fi
	@docker container prune -f
	@docker image prune -af
	@docker builder prune -af

# ---------------------------------------------------------
# Release
# ---------------------------------------------------------
# main makes a release, RELEASE_BRANCH=alpha or beta a prerelease. See .github/workflows/release.yml.
RELEASE_BRANCH ?= main

release-dry-run:
	@echo "==============================================================================="
	@echo "Starting the Release workflow on $(RELEASE_BRANCH) as a dry run: CI, then the next version ..."
	@echo "==============================================================================="
	gh workflow run release.yml --ref $(RELEASE_BRANCH) -f dry_run=true
	@echo "Follow it with: gh run watch"

release:
	@echo "==============================================================================="
	@echo "Starting the Release workflow on $(RELEASE_BRANCH): CI, then semantic-release ..."
	@echo "==============================================================================="
	gh workflow run release.yml --ref $(RELEASE_BRANCH) -f dry_run=false
	@echo "Follow it with: gh run watch"

help:
	@echo '===================================================================='
	@echo 'init                   - Create venv from requirements/local.txt and install the git hooks'
	@echo 'python-requirements    - Compile requirements/in/*.in into the pinned requirements/*.txt, and install them'
	@echo 'check-python           - Verify that $(PYTHON) is installed'
	@echo 'test                   - Run the unit tests'
	@echo 'coverage               - Run the unit tests with a coverage report, and write coverage.xml'
	@echo 'run                    - Run the app interactively'
	@echo 'clean                  - Remove build, test and coverage artifacts'
	@echo '<************************** Code Management **************************>'
	@echo 'lint                   - Run all code linters and formatters'
	@echo 'analyze                - Generate code analysis report using cloc'
	@echo 'pre-commit-init        - Install and configure pre-commit'
	@echo 'pre-commit-run         - Run all pre-commit hooks on all files'
	@echo '<************************** Docker **************************>'
	@echo 'docker-build           - Build the Docker image'
	@echo 'docker-push            - Push the Docker image to DockerHub'
	@echo 'docker-run             - Run the Docker image'
	@echo 'docker-test            - Run the unit tests in the Docker image'
	@echo 'docker-prune           - Stop all containers and remove unused Docker objects'
	@echo '<************************** Release **************************>'
	@echo 'release-dry-run        - Run the Release workflow as a dry run: CI, then the next version'
	@echo 'release                - Release: CI, tag, GitHub release (RELEASE_BRANCH, default main)'
	@echo '===================================================================='
