SHELL := /bin/bash
REPO_NAME := agentic-ai-workflow

# The app and its MariaDB course database run in one Docker container. See the Dockerfile.
CONTAINER := $(REPO_NAME)

# scaffold .env from .env.example on first use. The Docker targets read it.
ifeq ("$(wildcard .env)","")
    $(shell cp .env.example .env)
endif
include .env

IMAGE := ${DOCKERHUB_USERNAME}/${REPO_NAME}

.PHONY: all help test coverage run python-requirements clean \
	lint analyze pre-commit-init pre-commit-run \
	docker-check docker-build docker-init docker-start docker-run docker-test docker-coverage \
	docker-push docker-prune \
	release-dry-run release

# Default target executed when no arguments are given to make.
all: help

# ---------------------------------------------------------
# Development
# ---------------------------------------------------------
# Everything runs in the Docker container that make docker-init creates.
test: docker-test

coverage: docker-coverage

run: docker-run

# requirements/in/*.in, each starting with -r constraints.in, compile into the pinned requirements/*.txt.
# pip-compile runs in a throwaway Python container, with the same Python as the Dockerfile.
python-requirements:
	@echo "==============================================================================="
	@echo "Compiling and updating Python dependency files using pip-compile ..."
	@echo "==============================================================================="
	make docker-check
	docker run --rm -v "$(CURDIR):/src" -w /src python:3.13-slim-trixie sh -c \
		'pip install --quiet "pip-tools>=7.5.0" && \
		pip-compile requirements/in/base.in -o requirements/base.txt && \
		pip-compile requirements/in/local.in -o requirements/local.txt'

clean:
	@echo "==============================================================================="
	@echo "Removing build, test and coverage artifacts ..."
	@echo "==============================================================================="
	rm -rf build dist .pytest_cache .mypy_cache .coverage coverage.xml coverage.out htmlcov node_modules
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

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

# pre-commit runs on the host, from your PATH, e.g. after pipx install pre-commit or brew install pre-commit.
pre-commit-init:
	@echo "==============================================================================="
	@echo "Installing and configuring pre-commit ..."
	@echo "==============================================================================="
	pre-commit install
	pre-commit autoupdate

pre-commit-run:
	@echo "==============================================================================="
	@echo "Running pre-commit hooks on all files ..."
	@echo "==============================================================================="
	pre-commit run --all-files

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
	docker build -t $(IMAGE) . --build-arg ENVIRONMENT=${ENVIRONMENT}

# Build the image, (re)create the container, and create the course database in its MariaDB.
# The container mounts ./app and pyproject.toml, so code changes reach it without a rebuild.
# MariaDB's root user logs in through the Unix socket and ignores its password, but
# create-course-database.sh needs one in MYSQL_PWD for any container but smarter-mariadb.
docker-init:
	@echo "==============================================================================="
	@echo "Creating the $(CONTAINER) container and its course database ..."
	@echo "==============================================================================="
	make docker-build
	docker rm -f $(CONTAINER) >/dev/null 2>&1 || true
	docker run -d --name $(CONTAINER) \
		-v "$(CURDIR)/app:/dist/app" \
		-v "$(CURDIR)/pyproject.toml:/dist/pyproject.toml:ro" \
		$(IMAGE)
	@echo "Waiting for MariaDB to start ..."
	@for i in $$(seq 1 30); do \
		docker exec $(CONTAINER) mariadb-admin ping --silent >/dev/null 2>&1 && exit 0; \
		sleep 1; \
	done; \
	echo >&2 "MariaDB didn't start. See: docker logs $(CONTAINER)"; exit 1
	MYSQL_PWD=unix-socket scripts/create-course-database.sh --container $(CONTAINER)

# Start the container if it is stopped, e.g. after a restart of Docker.
docker-start:
	make docker-check
	@docker start $(CONTAINER) >/dev/null 2>&1 || { echo >&2 "There's no $(CONTAINER) container. Run make docker-init first."; exit 1; }

docker-run: docker-start
	docker exec -it $(DOCKER_ENV) $(CONTAINER) python -m app.agent

docker-test: docker-start
	@echo "==============================================================================="
	@echo "Running the unit tests ..."
	@echo "==============================================================================="
	docker exec $(DOCKER_ENV) $(CONTAINER) python -m unittest discover -s app/

docker-coverage: docker-start
	@echo "==============================================================================="
	@echo "Running the unit tests with a coverage report ..."
	@echo "==============================================================================="
	docker exec $(DOCKER_ENV) $(CONTAINER) coverage run -m unittest discover -s app/
	docker exec $(CONTAINER) coverage report
	docker exec $(CONTAINER) coverage xml
	docker cp $(CONTAINER):/dist/coverage.xml coverage.xml

docker-push:
	@echo "==============================================================================="
	@echo "Pushing the Docker image to DockerHub ..."
	@echo "==============================================================================="
	make docker-check
	docker tag $(IMAGE) $(IMAGE):latest
	echo "${DOCKERHUB_ACCESS_TOKEN}" | docker login --username=${DOCKERHUB_USERNAME} --password-stdin
	docker push $(IMAGE):latest

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
	@echo 'test                   - Run the unit tests in the container (make docker-test)'
	@echo 'coverage               - Run the unit tests with a coverage report, and write coverage.xml (make docker-coverage)'
	@echo 'run                    - Run the app interactively in the container (make docker-run)'
	@echo 'python-requirements    - Compile requirements/in/*.in into the pinned requirements/*.txt'
	@echo 'clean                  - Remove build, test and coverage artifacts'
	@echo '<************************** Code Management **************************>'
	@echo 'lint                   - Run all code linters and formatters'
	@echo 'analyze                - Generate code analysis report using cloc'
	@echo 'pre-commit-init        - Install and configure pre-commit'
	@echo 'pre-commit-run         - Run all pre-commit hooks on all files'
	@echo '<************************** Docker **************************>'
	@echo 'docker-init            - Build the image, create the container and its course database'
	@echo 'docker-build           - Build the Docker image'
	@echo 'docker-start           - Start the container if it is stopped'
	@echo 'docker-run             - Run the app interactively in the container'
	@echo 'docker-test            - Run the unit tests in the container'
	@echo 'docker-coverage        - Run the unit tests with a coverage report in the container, and copy out coverage.xml'
	@echo 'docker-push            - Push the Docker image to DockerHub'
	@echo 'docker-prune           - Stop all containers and remove unused Docker objects'
	@echo '<************************** Release **************************>'
	@echo 'release-dry-run        - Run the Release workflow as a dry run: CI, then the next version'
	@echo 'release                - Release: CI, tag, GitHub release (RELEASE_BRANCH, default main)'
	@echo '===================================================================='
