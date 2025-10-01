# Use the official Python image from the Docker Hub.
# This runs on Debian Linux.
FROM python:3.13-slim-trixie AS base

LABEL maintainer="Lawrence McDaniel <lpm0073@gmail.com>" \
  description="Docker image for the StackademyAssistent" \
  license="GNU AGPL v3" \
  vcs-url="https://github.com/FullStackWithLawrence/agentic-ai-workflow" \
  org.opencontainers.image.title="StackademyAssistent" \
  org.opencontainers.image.version="0.1.0" \
  org.opencontainers.image.authors="Lawrence McDaniel <lpm0073@gmail.com>" \
  org.opencontainers.image.url="https://FullStackWithLawrence.github.io/smarter/" \
  org.opencontainers.image.source="https://github.com/FullStackWithLawrence/agentic-ai-workflow" \
  org.opencontainers.image.documentation="https://FullStackWithLawrence.github.io/smarter/"


FROM base AS requirements

# Set the working directory to /app
WORKDIR /dist

# Copy the current directory contents into the container at /app
COPY requirements/prod.txt requirements.txt

# Set environment variables
ENV ENVIRONMENT=dev
ENV PYTHONPATH=/dist

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

FROM requirements AS app

WORKDIR /dist
COPY app /dist/app

FROM app AS runtime

# Run the application when the container launches
CMD ["python", "-m", "app.agent"]
