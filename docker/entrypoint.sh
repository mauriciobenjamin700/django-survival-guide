#!/bin/sh
# Container startup: apply migrations, collect static files, then run the
# process passed as CMD (gunicorn by default). Fails fast on any error.
set -e

python manage.py migrate --no-input
python manage.py collectstatic --no-input

exec "$@"
