# ── Build Stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Production Stage ──────────────────────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=edu_analytics.settings.prod \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . .

RUN mkdir -p /app/staticfiles /app/media /app/ml_models /app/logs

RUN python manage.py collectstatic --noinput || true

RUN addgroup --system app && adduser --system --group app

RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py shell -c \"from django.contrib.auth import get_user_model; User=get_user_model(); u, created = User.objects.get_or_create(email='admin@edu.com'); u.set_password('admin123'); u.is_staff=True; u.is_superuser=True; u.is_active=True; u.save(); print('Admin ready')\" && gunicorn edu_analytics.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 1 --timeout 180"]
