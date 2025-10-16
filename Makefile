
SHELL := /bin/bash
REPO_NAME := agentic-ai-workflow

ifeq ($(OS),Windows_NT)
	PYTHON = python.exe
	ACTIVATE_VENV = venv\Scripts\activate
else
	PYTHON = python3.13
	ACTIVATE_VENV = source venv/bin/activate
endif
PIP = $(PYTHON) -m pip

ifneq ("$(wildcard .env)","")
	include .env
else
	$(shell cp .env-example .env)
endif

.PHONY: analyze pre-commit init lint clean test build release

# Default target executed when no arguments are given to make.
all: help

analyze:
	cloc . --exclude-ext=svg,json,zip --vcs=git

release:
	git commit -m "fix: force a new release" --allow-empty && git push

# -------------------------------------------------------------------------
# Install and run pre-commit hooks
# -------------------------------------------------------------------------
pre-commit:
	pre-commit install
	pre-commit autoupdate
	pre-commit run --all-files

# ---------------------------------------------------------
# create python virtual environments for prod
# ---------------------------------------------------------
init:
	make clean
	$(PYTHON) -m venv venv && \
	$(ACTIVATE_VENV) && \
	$(PIP) install --upgrade pip && \
	$(PIP) install -r requirements/prod.txt && \
	deactivate

# ---------------------------------------------------------
# create python virtual environments for dev
# ---------------------------------------------------------
init-dev:
	make init && \
	npm install && \
	$(ACTIVATE_VENV) && \
	$(PIP) install -r requirements/local.txt && \
	deactivate && \
	pre-commit install

test:
	python -m unittest discover -s app/

coverage:
	python -m coverage run --source=app --omit='app/tests/*' -m unittest discover -s app/tests
	python -m coverage report -m --omit='app/tests/*'
	python -m coverage xml --omit='app/tests/*'

lint:
	isort .
	pre-commit run --all-files
	black .
	flake8 ./app/
	pylint ./app/**/*.py

clean:
	rm -rf venv node_modules app/__pycache__ package-lock.json

docker-build:
	docker build -t ${DOCKERHUB_USERNAME}/${REPO_NAME} . --build-arg ENVIRONMENT=${ENVIRONMENT}

docker-push:
	source .env && \
	docker tag ${DOCKERHUB_USERNAME}/${REPO_NAME} ${DOCKERHUB_USERNAME}/${REPO_NAME}:latest && \
	echo "${DOCKERHUB_ACCESS_TOKEN}" | docker login --username=${DOCKERHUB_USERNAME} --password-stdin && \
	docker push ${DOCKERHUB_USERNAME}/${REPO_NAME}:latest

docker-run:
	docker run -it -e OPENAI_API_KEY=${OPENAI_API_KEY} \
		-e ENVIRONMENT=prod \
		-e MYSQL_HOST=${MYSQL_HOST} \
		-e MYSQL_PORT=${MYSQL_PORT} \
		-e MYSQL_USER=${MYSQL_USER} \
		-e MYSQL_PASSWORD=${MYSQL_PASSWORD} \
		-e MYSQL_DATABASE=${MYSQL_DATABASE} \
		-e MYSQL_CHARSET=${MYSQL_CHARSET} \
		-e LOGGING_LEVEL=${LOGGING_LEVEL} \
		-e LLM_TOOL_CHOICE=${LLM_TOOL_CHOICE} ${DOCKERHUB_USERNAME}/${REPO_NAME}:latest

docker-test:
	docker run --rm \
		-e OPENAI_API_KEY=${OPENAI_API_KEY} \
		-e ENVIRONMENT=local \
		-e MYSQL_HOST=${MYSQL_HOST} \
		-e MYSQL_PORT=${MYSQL_PORT} \
		-e MYSQL_USER=${MYSQL_USER} \
		-e MYSQL_PASSWORD=${MYSQL_PASSWORD} \
		-e MYSQL_DATABASE=${MYSQL_DATABASE} \
		-e MYSQL_CHARSET=${MYSQL_CHARSET} \
		-e LOGGING_LEVEL=${LOGGING_LEVEL} \
		-e LLM_TOOL_CHOICE=${LLM_TOOL_CHOICE} \
		${DOCKERHUB_USERNAME}/${REPO_NAME}:latest \
		python -m unittest discover -s app/

docker-coverage:
	docker run --rm \
		-e OPENAI_API_KEY=${OPENAI_API_KEY} \
		-e ENVIRONMENT=local \
		-e MYSQL_HOST=${MYSQL_HOST} \
		-e MYSQL_PORT=${MYSQL_PORT} \
		-e MYSQL_USER=${MYSQL_USER} \
		-e MYSQL_PASSWORD=${MYSQL_PASSWORD} \
		-e MYSQL_DATABASE=${MYSQL_DATABASE} \
		-e MYSQL_CHARSET=${MYSQL_CHARSET} \
		-e LOGGING_LEVEL=${LOGGING_LEVEL} \
		-e LLM_TOOL_CHOICE=${LLM_TOOL_CHOICE} \
		${DOCKERHUB_USERNAME}/${REPO_NAME}:latest \
		/bin/bash -c "python -m coverage run --source=app --omit='app/tests/*' -m unittest discover -s app/tests && python -m coverage report -m --omit='app/tests/*' && python -m coverage xml --omit='app/tests/*'"

docker-prune:
	@if [ "`docker ps -aq`" ]; then \
		docker stop $(docker ps -aq); \
	fi
	@docker container prune -f
	@docker image prune -af
	@docker builder prune -af

######################
# HELP
######################
help:
	@echo '===================================================================='
	@echo 'analyze			- generate code analysis report'
	@echo 'release			- force a new GitHub release'
	@echo 'init			- create a Python virtual environment and install prod dependencies'
	@echo 'init-dev		- install dev dependencies'
	@echo 'test			- run Python unit tests'
	@echo 'lint			- run Python linting'
	@echo 'clean			- destroy the Python virtual environment'
	@echo 'pre-commit		- install and run pre-commit hooks'
	@echo 'docker-build		- build the Docker image'
	@echo 'docker-run		- run the Docker image'
	@echo 'docker-test		- run the Docker image for testing'
	@echo 'docker-coverage		- run the Docker image for testing + coverage report'
	@echo 'docker-push		- push the Docker image to DockerHub'
	@echo 'docker-prune		- remove unused Docker containers/images/builders'
