#!/bin/sh
# Arranque del contenedor: migraciones, seed opcional y servidor.
set -e

alembic upgrade head

if [ "${SEED_DATABASE:-false}" = "true" ]; then
    python scripts/seed_models.py
fi

# uvicorn arranca primero con su logging; la app lo redirige a JSON al importarse.
exec uvicorn main:app --host 0.0.0.0 --port 8010
