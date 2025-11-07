#!/usr/bin/env bash
set -euo pipefail

# Optional: run collectstatic if explicitly enabled
if [ "${COLLECT_STATIC:-false}" = "true" ]; then
  echo "Running collectstatic..."
  python manage.py collectstatic --noinput
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
