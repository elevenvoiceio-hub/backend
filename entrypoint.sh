#!/usr/bin/env bash
set -euo pipefail

# Optional: run collectstatic if explicitly enabled
if [ "${COLLECT_STATIC:-false}" = "true" ]; then
  echo "Running collectstatic..."
  python manage.py collectstatic --noinput
fi

# Optional: run migrations at startup. Controlled by RUN_MIGRATIONS env var.
# Set RUN_MIGRATIONS=false to skip running migrations in environments where
# you prefer running them separately (e.g. via a Cloud Run Job or CI step).
#
# You can optionally run `makemigrations` before `migrate` by setting
# RUN_MAKE_MIGRATIONS=true. Note: migration files created at runtime are
# ephemeral (won't be committed to source control) unless you capture and
# commit them back to your repository.
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Starting migration step..."

  if [ "${RUN_MAKE_MIGRATIONS:-false}" = "true" ]; then
    echo "Running makemigrations (generate migration files)..."
    if ! python manage.py makemigrations --noinput; then
      echo "Warning: makemigrations failed. Exiting with non-zero status to avoid running the app in a bad state."
      exit 1
    fi
  fi

  echo "Running database migrate..."
  if ! python manage.py migrate --noinput; then
    echo "Warning: migrate failed. Exiting with non-zero status to avoid running the app in a bad state."
    exit 1
  fi
fi

# Optional: print which port we'll bind to (helps debugging)
echo "Starting service on port ${PORT:-8080}"

# If the entrypoint is invoked with additional args, run them (useful for overrides)
if [ "$#" -gt 0 ]; then
  exec "$@"
else
  # Default: run gunicorn and bind to the PORT env var (fall back to 8080)
  exec gunicorn VoiceAsService.wsgi:application \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 2 \
    --threads 2 \
    --log-level info \
    --timeout 120
fi
