# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# Run as an unprivileged user (uid 10001).
USER 10001

EXPOSE 8000

# Uses urllib from the stdlib so no extra package (curl/wget) is required.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request as u; raise SystemExit(0 if u.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"]

# Apply Alembic migrations before the API starts serving traffic.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]