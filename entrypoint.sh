#!/usr/bin/env bash
set -euo pipefail

# default: do not run migrations automatically in every container
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  python manage.py migrate --noinput
fi

if [ "${COLLECT_STATIC:-false}" = "true" ]; then
  python manage.py collectstatic --noinput
fi

exec "$@"
