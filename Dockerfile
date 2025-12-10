FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1

WORKDIR /app

# Install build dependencies and fonts
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    pkg-config \
    libglib2.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    fonts-noto-cjk \
    fontconfig

# Update font cache
RUN fc-cache -fv

RUN rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY uv.lock pyproject.toml $HOME/app/

# Install Python dependencies with uv
RUN uv sync --frozen || uv sync
