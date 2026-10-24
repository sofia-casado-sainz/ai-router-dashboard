# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN useradd --create-home --uid 10001 app

COPY . .
RUN pip install .

USER app
EXPOSE 8010

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8010/api/v1/health', timeout=2)"

# Aplica las migraciones (y el seed si SEED_DATABASE=true) antes de arrancar uvicorn.
CMD ["sh", "scripts/docker-entrypoint.sh"]
