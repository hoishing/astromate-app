# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install build dependencies, git, and uv
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with Git authentication
RUN --mount=type=secret,id=github_token \
    if [ -f /run/secrets/github_token ]; then \
        export GIT_TOKEN=$(cat /run/secrets/github_token) && \
        git config --global url."https://${GIT_TOKEN}@github.com/".insteadOf "https://github.com/"; \
    fi && \
    uv sync --frozen && \
    git config --global --unset url."https://${GIT_TOKEN}@github.com/".insteadOf || true

# Copy application files
COPY . .

# Expose port
EXPOSE 8508

# Run the Streamlit app
CMD ["uv", "run", "streamlit", "run", "main.py", "--server.port", "8508", "--server.address", "0.0.0.0"]
