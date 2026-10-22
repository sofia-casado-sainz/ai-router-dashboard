import json

import pytest

from main import app
from scripts.export_openapi import CONTRACT_PATH


@pytest.mark.skipif(not CONTRACT_PATH.exists(), reason="contracts/ no está disponible (p. ej. en Docker)")
def test_openapi_contract_is_up_to_date() -> None:
    committed = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert committed == app.openapi(), (
        "contracts/openapi.json está desactualizado: ejecuta `python scripts/export_openapi.py`"
    )
