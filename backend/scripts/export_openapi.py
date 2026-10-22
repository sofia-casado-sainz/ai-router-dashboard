"""Exporta el esquema OpenAPI de FastAPI a contracts/openapi.json.

Uso (desde backend/):  python scripts/export_openapi.py
Ejecutarlo tras cambiar cualquier endpoint o schema; el test de contrato falla
si el archivo versionado no coincide con la API.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
CONTRACT_PATH = BACKEND_DIR.parent / "contracts" / "openapi.json"


def render_openapi() -> str:
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    from main import app

    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(render_openapi(), encoding="utf-8")
    print(f"OpenAPI exportado en {CONTRACT_PATH}")


if __name__ == "__main__":
    main()
