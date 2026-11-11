# Use the official Python image from the Docker Hub.
# This runs on Debian Linux.
#
# The image holds the app and a MariaDB server for its course database. The
# container runs MariaDB, and you run the app inside it with docker exec. See
# make docker-init, which also creates the database with
# scripts/create-course-database.sh.
FROM python:3.13-slim-trixie AS base

LABEL maintainer="Lawrence McDaniel <lpm0073@gmail.com>" \
  description="Docker image for the StackademyAssistent" \
  license="GNU AGPL v3" \
  vcs-url="https://github.com/FullStackWithLawrence/agentic-ai-workflow" \
  org.opencontainers.image.title="StackademyAssistent" \
  org.opencontainers.image.version="0.1.8-alpha.2" \
  org.opencontainers.image.authors="Lawrence McDaniel <lpm0073@gmail.com>" \
  org.opencontainers.image.url="https://FullStackWithLawrence.github.io/agentic-ai-workflow/" \
  org.opencontainers.image.source="https://github.com/FullStackWithLawrence/agentic-ai-workflow" \
  org.opencontainers.image.documentation="https://FullStackWithLawrence.github.io/agentic-ai-workflow/"


# Environment: local, alpha, beta, next, or production
ARG ENVIRONMENT=local
ENV ENVIRONMENT=$ENVIRONMENT
RUN echo "ENVIRONMENT: $ENVIRONMENT"

FROM base AS mariadb

# MariaDB server and client. Debian's package creates an empty data directory in
# /var/lib/mysql, and a root user that logs in through the Unix socket, so
# docker exec can run the mariadb client as root without a password.
RUN apt-get update && \
  apt-get install -y --no-install-recommends mariadb-server mariadb-client && \
  rm -rf /var/lib/apt/lists/* && \
  mkdir -p /run/mysqld && \
  chown mysql:mysql /run/mysqld

FROM mariadb AS requirements

# Set the working directory to /app
WORKDIR /dist

# Copy the current directory contents into the container at /app
COPY requirements/base.txt base.txt
COPY requirements/local.txt local.txt

# Set environment variables
ENV PYTHONPATH=/dist

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r base.txt

# Install Python dependencies for the local environment for cases where
# we're going to run python unit tests in the Docker container.
RUN if [ "$ENVIRONMENT" = "local" ] ; then pip install -r local.txt ; fi


FROM requirements AS app

WORKDIR /dist
# pyproject.toml holds coverage's settings, for make docker-coverage.
COPY pyproject.toml /dist/pyproject.toml
COPY app /dist/app

FROM app AS runtime

# MariaDB listens on 127.0.0.1:3306 inside the container, which is where
# MYSQL_HOST and MYSQL_PORT in .env.example point. The app runs in the same
# container, so the port isn't published to the host.
#
# Run MariaDB in the foreground, so that the container keeps running. Start the
# app in it with: docker exec -it agentic-ai-workflow python -m app.agent
CMD ["mariadbd", "--user=mysql"]
