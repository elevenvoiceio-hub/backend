# ---------- builder stage ----------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# System deps needed to build Python packages (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl git \
  && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first for better caching
COPY requirements.txt /app/requirements.txt

# Install wheels and dependencies into system python
RUN python -m pip install --upgrade pip setuptools wheel \
  && pip install -r /app/requirements.txt

# ---------- runtime stage ----------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    # default port Cloud Run expects 8080 (you can override at runtime)
    PORT=8080

WORKDIR /app

# Runtime system deps (lighter than builder)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 ca-certificates bash \
  && rm -rf /var/lib/apt/lists/*

# Copy installed site-packages & binaries from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY . /app

# Ensure entrypoint exists and is executable (do this as root)
# This avoids permission-denied at runtime.
RUN chmod +x /app/entrypoint.sh || true

# Create non-root user, adjust ownership and ensure /app is writable by user
RUN useradd --create-home appuser \
  && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

# Use the entrypoint script to start the app. It will exec the gunicorn server if no args provided.
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
