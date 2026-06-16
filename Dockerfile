# =========================
# Stage 1: Build React frontend
# =========================
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build


# =========================
# Stage 2: Build Django backend
# =========================
FROM python:3.11-slim AS backend-runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=scholarmind_backend.settings

WORKDIR /app/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


COPY backend/ ./

RUN mkdir -p static/frontend

COPY --from=frontend-builder /app/frontend/dist/ static/frontend/

RUN python manage.py collectstatic --noinput

EXPOSE 10000

CMD ["sh", "-c", "python manage.py migrate && echo Starting Gunicorn on port ${PORT:-10000} && exec gunicorn scholarmind_backend.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 300 --access-logfile - --error-logfile -"]