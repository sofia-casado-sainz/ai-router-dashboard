# Contrato frontend ↔ backend

`openapi.json` es el esquema OpenAPI exportado desde FastAPI y la **fuente de verdad** del contrato HTTP.

## Flujo actual (Sprint S0)

1. Cambias un endpoint o schema en `backend/`.
2. Regeneras el contrato desde `backend/`:

   ```bash
   python scripts/export_openapi.py
   ```

3. Actualizas a mano `frontend/src/types/api.ts`, que es el único archivo del frontend con tipos del API.

El test `backend/tests/test_contract.py` falla si `openapi.json` no coincide con la API real, así que el contrato no puede quedarse desactualizado sin que se note.

## Flujo previsto (Sprint S1)

`frontend/src/types/api.ts` dejará de mantenerse a mano y se generará desde `openapi.json` (por ejemplo, con `openapi-typescript`).

Los `operationId` ya son estables (`get_health`, `route_prompt`), así que los nombres generados no cambiarán al refactorizar funciones en Python.
