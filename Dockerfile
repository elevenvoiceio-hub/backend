# ---------- builder stage ----------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps needed to build Python packages (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl git \
  && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first for better caching
COPY requirements.txt /app/requirements.txt

# Install wheels and dependencies into system python
RUN pip install --upgrade pip setuptools wheel \
  && pip install -r /app/requirements.txt

# ---------- runtime stage ----------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    # default port Cloud Run expects 8080 (you can override at runtime)
    PORT=8080

WORKDIR /app

# Install runtime system deps (lighter than builder)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Copy installed site-packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY . /app

# Create non-root user and set permissions
RUN useradd --create-home appuser \
  && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

# Add an entrypoint script (see entrypoint.sh below)
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command: serve with gunicorn
CMD ["gunicorn", "VoiceAsService.wsgi:application", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--threads", "2", \
     "--log-level", "info", \
     "--timeout", "120"]
