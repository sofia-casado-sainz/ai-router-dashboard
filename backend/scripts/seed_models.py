"""Carga el catálogo de modelos de ejemplo en la base de datos configurada.

Uso (desde backend/, tras `alembic upgrade head`):  python scripts/seed_models.py
Es idempotente: se puede ejecutar varias veces sin duplicar datos.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


async def run() -> None:
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    from core.config import get_settings
    from database.seed import seed_model_catalog
    from database.session import create_engine, create_session_factory

    engine = create_engine(get_settings())
    try:
        async with create_session_factory(engine)() as session:
            result = await seed_model_catalog(session)
    finally:
        await engine.dispose()
    print(
        f"Seed completado: {result.models_created} modelos y {result.prices_created} precios nuevos; "
        f"{result.execution_targets_filled} modelos existentes con ejecución completada."
    )


if __name__ == "__main__":
    asyncio.run(run())
