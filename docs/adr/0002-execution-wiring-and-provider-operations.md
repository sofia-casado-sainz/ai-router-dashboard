# ADR 0002: Execution Wiring and Provider Operations

- **Fecha:** 2026-10-24
- **Sprint:** S2b · OpenRouter Foundation
- **Decide:** Sofía Casado Sainz
- **Amplía:** [ADR-0001](0001-inference-provider-abstraction.md)

## Status

**Aceptado.** Amplía ADR-0001; donde difieran, prevalece este ADR. Cada decisión indica la fase en la que se implementa.

## Context

ADR-0001 definió la abstracción de inference providers. S2a la implementó (`16be2c4`…`616fd05` y `f0b250c`…`ff280d4`), con decisiones aprobadas durante la implementación que ADR-0001 no recoge.

La auditoría de S2a encontró:

- **Desajustes entre ADR-0001 y el código:** el estado decía que nada estaba implementado, no figuraban los puertos ni las decisiones de S2a, y el registro no se construye desde la configuración (E1–E4).
- **Un contrato de errores incorrecto en `POST /api/v1/completions`:** un 422 con dos formas distintas y respuestas de error sin esquema (E5, E6).
- **Riesgos operativos:** el catálogo apunta a `fake` (R1), `FakeProvider` se registra siempre (R2) y los proveedores no tienen ciclo de vida (R3).

Este ADR registra esas decisiones y las nuevas para cerrar la fase.

## Decision

### 0. Fases

| Fase | Contenido |
|---|---|
| **S2a** · Execution Foundation | Implementada: abstracción, capa de ejecución, catálogo con `inference_provider`, `POST /api/v1/completions` con `FakeProvider`. |
| **S2b** · OpenRouter Foundation | **S2b-1** (arquitectura y operación): este ADR, contrato de errores, trazabilidad, ciclo de vida, registro desde configuración. **S2b-2** (OpenRouter): `OpenRouterProvider` con transporte simulado, sustitución simulada, migración del catálogo, coste estimado, timeouts, y el control de exposición de ADR-0003. |
| **S2c** · Router on the Catalog | El router lee el catálogo persistente y desaparece el mapeo transitorio (lo que ADR-0001 llamaba S2b). Necesita su propio ADR. |

### 1. Puertos `Decider` y `ModelResolver` (S2a)

`ExecutionService.execute()` decide, resuelve y ejecuta a través de dos puertos inyectados, definidos en `domain/execution.py`:

- `Decider`: implementado por `RouterDecider`, que reutiliza `route_prompt()`.
- `ModelResolver`: implementado por `CatalogModelResolver`, que contiene el mapeo transitorio de ADR-0001.

Así `ExecutionService` sigue sin depender de FastAPI, SQLAlchemy, HTTP ni del router. Dos tests de arquitectura lo comprueban. El diagrama de ADR-0001, en el que `ExecutionService` llama al router directamente, se lee a través de estos puertos.

### 2. Catálogo y seed (S2a)

- La migración `0002` añade `inference_provider` y `provider_model_id` a `models`. Son opcionales y deben estar ambos o ninguno.
- Los modelos de ejemplo ejecutables se cargan con `inference_provider="fake"` y `provider_model_id=model_key`. Ollama Local no es ejecutable.
- En filas existentes, el seed solo rellena esos campos si ambos están vacíos y nunca sobrescribe valores.

### 3. Endpoint siempre presente (S2a)

`POST /api/v1/completions` existe siempre. Mientras `COMPLETIONS_ENABLED=false`, valor por defecto, responde 503.

### 4. `GET /api/v1/models` sin cambios (S2a)

No expone `inference_provider` ni `provider_model_id` todavía. El contrato de S1 se mantiene.

### 5. Contrato de errores (S2b-1)

Todas las respuestas de error de la API, salvo la validación de la petición, usan `ErrorResponse`:

```text
ErrorResponse { detail: string, code: string, request_id: string | null }
```

| Caso | HTTP | `code` |
|---|---|---|
| Ejecución desactivada | 503 | `completions_disabled` |
| `ProviderNotConfigured` | 503 | `provider_not_configured` |
| `ProviderUnavailable` | 503 | `provider_unavailable` |
| `ProviderTimeout` | 504 | `provider_timeout` |
| `ProviderRateLimited` | 429 | `provider_rate_limited` |
| `ProviderAuthError` | 502 | `provider_auth_error` |
| `ProviderBadRequest` | **400** | `provider_bad_request` |
| `ModelNotAvailable` | 502 | `model_not_available` |
| Base de datos del catálogo no disponible | 503 | `catalog_unavailable` |
| Otro `ProviderError` | 502 | `provider_error` |

- **`ProviderBadRequest` pasa de 422 a 400.** Cambia la tabla de ADR-0001: 422 queda reservado a la validación de la petición, con el esquema `HTTPValidationError` de FastAPI.
- **`detail` es un mensaje fijo por `code`.** El mensaje original de un proveedor nunca llega al cliente: queda en el log, correlacionado por `request_id`.
- **`Retry-After`** se redondea hacia arriba, con un mínimo de 1 segundo.
- **`code` es estable:** los clientes deben usarlo en lugar de interpretar `detail`.
- `GET /api/v1/models` adopta `ErrorResponse` en su 503, con el mismo `detail` que tenía.

### 6. Trazabilidad (S2b-1)

- Cada petición tiene un `request_id`. Se acepta el `X-Request-ID` entrante si es válido (1–64 caracteres de `[A-Za-z0-9._-]`); si no, se genera uno.
- Se devuelve en la cabecera `X-Request-ID` de todas las respuestas y en `ErrorResponse.request_id`. CORS la expone al navegador.
- Se guarda en un `contextvar`. Un filtro de logging lo añade a todos los logs emitidos durante la petición.
- Llega a `CompletionRequest.request_id`. El log de cada ejecución incluye `request_id`, `inference_provider`, `provider_model_id` y `provider_request_id`.
- **Nunca se registra el prompt.**
- El middleware es ASGI puro, no `BaseHTTPMiddleware`, para que el contexto se propague sin depender de cómo se crean las tareas.

### 7. Ciclo de vida de los proveedores (S2b-1)

- `InferenceProvider` añade `async def aclose()`. Debe ser idempotente; en `FakeProvider` no hace nada.
- `ProviderRegistry.aclose()` cierra todos los proveedores. Un fallo al cerrar uno se registra y no impide cerrar el resto. Después, el registro queda vacío.
- El `lifespan` de la aplicación cierra el registro al parar.
- Los proveedores se siguen construyendo en `create_app()`: un cliente `httpx.AsyncClient` puede crearse fuera del bucle de eventos.

### 8. Registro desde la configuración (S2b-1)

- `SIMULATED_PROVIDERS` admite `true`, `false` o `auto` (por defecto; también vale vacío).
- **En automático,** los proveedores simulados están activos en `development` y `test`, y desactivados en `staging` y `production`. Una demo puede activarlos explícitamente.
- `FakeProvider` solo se registra si los proveedores simulados están activos. **No hay registros incondicionales.**
- Sin ningún proveedor, la aplicación arranca igual y `POST /api/v1/completions` responde 503 (`provider_not_configured`).
- Hasta S2b-2 el catálogo apunta a `fake`, así que en producción la ejecución no está disponible. Es el comportamiento seguro.

### 9. Sustitución simulada (S2b-2)

- Con los proveedores simulados activos y OpenRouter sin configurar, el registro resuelve la clave `openrouter` a `FakeProvider`.
- La sustitución se registra en el log al arrancar.
- El resultado sigue diciendo `inference_provider="fake"`: informa de quién lo ejecutó realmente.
- **Nunca ocurre en producción:** allí, sin clave de OpenRouter, la respuesta es 503.

### 10. Migración del catálogo `fake` → `openrouter` (S2b-2)

- Una migración `0003` actualiza solo las filas que conservan los valores originales del seed: `inference_provider="fake"`, `provider_model_id=model_key` y un modelo del conjunto de ejemplo.
- No toca cambios manuales, y el `downgrade` solo revierte filas que conserven los valores nuevos.
- **Es una excepción documentada** a la regla de S1 de no incluir datos en migraciones: corrige datos gestionados por el seed, de forma condicional y reversible.
- Los identificadores de OpenRouter se verifican contra su catálogo al implementarla. Un modelo de ejemplo sin equivalente real queda no ejecutable (ambos campos vacíos): nunca se inventa un identificador.
- El seed pasa a crear los modelos nuevos con `openrouter`.

### 11. Coste estimado desde el catálogo (S2b-2)

- `ResolvedModel` incluye el precio vigente del modelo, si lo tiene.
- Un proveedor que no informe del coste devuelve `cost=None`, y `ExecutionService` lo estima con el uso y el precio del catálogo (`estimated_from_catalog`).
- Sin uso o sin precio, el coste es nulo: nunca un número inventado.

### 12. Precedencia de timeouts (S2b-2)

- Los proveedores HTTP tienen timeouts de conexión y de lectura propios, menores que el timeout total de `ExecutionService`.
- Los dos se traducen a `ProviderTimeout`.
- Una configuración incoherente genera un aviso al arrancar, sin impedir el arranque.

### 13. `OpenRouterProvider` (S2b-2)

Pasa de "S2" en ADR-0001 a S2b-2, sin cambios en su diseño:

- base compatible con la API de OpenAI y `httpx`;
- tests con transporte simulado y sin llamadas externas;
- registro solo si existe `OPENROUTER_API_KEY`.

## Consequences

**Positivas**

- ADR-0001 y ADR-0002 describen juntos lo que existe y lo que falta, por fases.
- Los clientes reciben errores con un formato y un `code` estables, sin texto de terceros.
- Cada error y cada ejecución se pueden seguir en los logs por `request_id`.
- Producción no puede servir respuestas simuladas por accidente.
- Los proveedores con recursos (clientes HTTP) se cierran de forma ordenada.

**Negativas**

- Cambia un código HTTP ya publicado (`ProviderBadRequest`: 422 → 400), con un ajuste deliberado de los tests de `/completions`.
- Los mensajes de error son menos específicos en la respuesta: el detalle está en los logs.
- La sustitución simulada (S2b-2) añade una indirección en el registro que hay que documentar bien.
- La migración `0003` rompe a propósito la regla de "sin datos en migraciones".

## Alternatives considered

- **Mantener `ProviderBadRequest` en 422 y documentar un `oneOf`:** descartada. Un mismo código con dos formas complica a cualquier cliente generado desde el contrato.
- **Devolver el mensaje del proveedor tal cual:** descartada. Puede filtrar detalles internos del proveedor o de la cuenta.
- **Un catálogo distinto por entorno (`fake` en desarrollo, `openrouter` en producción):** descartada. El mismo dato significaría cosas distintas según el entorno, y el seed dependería del entorno.
- **Construir los proveedores en el `lifespan`:** descartada. Los tests que no ejecutan el `lifespan` dejarían de tener registro.
- **`BaseHTTPMiddleware` para el `request_id`:** descartada en favor de un middleware ASGI puro, más predecible con `contextvars`.
