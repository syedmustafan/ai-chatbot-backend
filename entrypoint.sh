#!/bin/sh
set -e
python manage.py migrate --noinput
exec gunicorn --bind :${PORT:-8080} --workers 2 --threads 8 --timeout 0 chatbot_project.wsgi:application
