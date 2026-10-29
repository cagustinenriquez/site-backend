# syntax=docker/dockerfile:1

# ---- Build stage: install dependencies with uv ----
FROM python:3.10-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install deps first so this layer is cached until the lockfile changes
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ---- Runtime stage: slim image without uv or build cache ----
FROM python:3.10-slim

RUN useradd --create-home --uid 1000 app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app main.py ./
COPY --chown=app:app app ./app
# Seed data; mount a volume at /app/data to persist posts
COPY --chown=app:app data ./data

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
