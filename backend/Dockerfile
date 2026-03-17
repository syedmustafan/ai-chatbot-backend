# Build stage not required for this app; single stage is enough.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .
RUN chmod +x entrypoint.sh

# Collect static files (optional; required if serving admin/static)
RUN python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Run migrations then Gunicorn (Cloud Run sets PORT)
CMD ["./entrypoint.sh"]
