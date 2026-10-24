# ADR 0001: Inference Provider Abstraction

- **Fecha:** 2026-10-24
- **Sprint:** S2 · OpenRouter Foundation
- **Decide:** Sofía Casado Sainz

## Status

**Aceptado. Implementado en S2a** (`16be2c4`…`616fd05` y `f0b250c`…`ff280d4`).

Ampliado por [ADR-0002](0002-execution-wiring-and-provider-operations.md) (decisiones de implementación y operación) y [ADR-0003](0003-exposure-gate-for-real-inference-providers.md) (requisitos antes de usar un proveedor real). Donde difieran, prevalecen esos ADRs. Este documento no se reescribe: las fases citadas aquí se corresponden con S2a, S2b (S2b-1 y S2b-2) y S2c según ADR-0002.

El anexo sobre licencia es una recomendación independiente de la arquitectura de proveedores. No modifica el archivo `LICENSE`; si se aprueba, se aplicará en su propio cambio.

## Context

**Estado actual (después de S1):**

- `POST /api/v1/route` decide qué modelo usar y explica por qué, pero no ejecuta nada. El Playground depende de esa respuesta, y `tests/test_route_compat.py` comprueba que no cambia.
- El router decide con reglas sobre su catálogo interno (`router/catalog.py`: `gpt`, `claude-sonnet`, `gemini`, `deepseek`), con precios simulados en € por cada 1.000 tokens.
- El catálogo persistente de S1 (tablas `models` y `model_prices`) guarda modelos de ejemplo con precios en USD por millón de tokens. En él, la columna `provider` identifica al **vendor** del modelo: `openai`, `anthropic`, `google`, `deepseek`, `ollama`.
- `ModelCatalogService` declara `sync_openrouter_models()` y `sync_ollama_models()`, sin implementar.

**Qué cambia en S2:** el sistema tiene que poder ejecutar el modelo elegido y devolver una respuesta. El primer sistema de ejecución será OpenRouter; después vendrán Ollama (S3) y otros.

**Lecciones previas que condicionan el diseño** (ver `docs/INCIDENTS.md`):

- Una configuración incorrecta no debe impedir que arranque toda la aplicación.
- Toda llamada de red necesita un timeout explícito; sin él, un servicio que no responde bloquea la petición durante decenas de segundos.
- Cada coste debe llevar su moneda: hoy conviven € y USD.

## Architectural Principles

1. **Routing and execution are separate concerns.**
   La capa de decisión elige el modelo; la capa de ejecución lo ejecuta. Ninguna conoce los detalles internos de la otra.
2. **Model vendors and inference providers are different concepts.**
   `provider` es quien crea el modelo (Anthropic); `inference_provider` es quien lo ejecuta para nosotros (OpenRouter, Ollama, `FakeProvider`).
3. **All execution backends must expose normalized types.**
   Cualquier proveedor devuelve `CompletionResult` y `CompletionChunk` con la misma forma, los mismos errores y el mismo tratamiento de uso y coste.
4. **Router decisions must remain provider-agnostic.**
   El router decide un modelo, no un proveedor de ejecución. Las reglas de decisión no mencionan OpenRouter ni Ollama.
5. **New inference providers must be pluggable without router modifications.**
   Añadir un proveedor consiste en implementar `InferenceProvider` y registrarlo en `ProviderRegistry`.
6. **External provider integrations must be isolated behind a stable interface.**
   Los formatos, errores y particularidades de cada API externa no salen de su implementación de `InferenceProvider`.
7. **Testing and demonstrations must not require paid inference providers.**
   Los tests, la CI y las demos funcionan con `FakeProvider`, sin claves, sin red y sin coste.

## Decision

### 1. Decision Layer y Execution Layer

Es el principio central de este ADR.

- **Decision Layer:** el router actual. `POST /api/v1/route` sigue existiendo exactamente igual y solo decide. El Playground no cambia.
- **Execution Layer:** `ExecutionService`, `ProviderRegistry` y las implementaciones de `InferenceProvider`. La expone un endpoint nuevo, `POST /api/v1/completions`, que decide **y** ejecuta.

```text
POST /api/v1/completions
  │
  ▼
ExecutionService                                   (Execution Layer)
  │ 1. decide(prompt)
  ├──────────► Router (sin cambios)                (Decision Layer)
  │              → id de modelo del router, p. ej. "deepseek"
  │ 2. resolve(router_id)
  ├──────────► Mapeo transitorio router_id → catalog_model   (deuda, ver más abajo)
  │              → inference_provider + provider_model_id
  │ 3. registry.get(inference_provider)
  ├──────────► ProviderRegistry → InferenceProvider
  │ 4. complete(CompletionRequest)
  └──────────► OpenRouterProvider | FakeProvider | …  → CompletionResult
  │
  ▼
Respuesta: la decisión (misma forma que /route) + el CompletionResult
```

`ExecutionService` no conoce HTTP ni proveedores concretos. Los proveedores no conocen las reglas de decisión.

### 2. Terminología: `inference_provider`

| Término | Significado | Ejemplos |
|---|---|---|
| `provider` (existente) | Vendor que crea el modelo | `openai`, `anthropic`, `google`, `deepseek` |
| `inference_provider` (nuevo) | Sistema que ejecuta el modelo | `openrouter`, `ollama`, `fake` y futuros sistemas de ejecución |

El catálogo persistente añadirá `inference_provider` y `provider_model_id` (el identificador del modelo en ese sistema de ejecución) mediante una migración nueva. `GET /api/v1/models` solo ganará campos, sin cambiar ni quitar los existentes. `provider` no se reutiliza ni cambia de significado.

### 3. Interfaz `InferenceProvider`

Protocolo asíncrono que implementa cada sistema de ejecución:

| Miembro | Responsabilidad | Uso en S2 |
|---|---|---|
| `key` | Identificador estable (`"openrouter"`, `"fake"`). Coincide con `inference_provider` en el catálogo. | Sí |
| `capabilities` | `streaming`, `local` (los datos no salen de la máquina del usuario), `reports_cost`, `lists_models` | Sí |
| `complete(CompletionRequest) → CompletionResult` | Una respuesta completa | Sí |
| `stream(CompletionRequest) → CompletionChunk…` | Respuesta por fragmentos | **No.** Forma parte del contrato desde S2 para no romper la interfaz cuando se implemente. Los proveedores que no lo soportan lo indican con `capabilities.streaming = false`. |
| `list_models()` | Catálogo del sistema de ejecución; base de `sync_openrouter_models()` y `sync_ollama_models()` | **No.** Forma parte del contrato desde S2. |
| `health()` | Disponibilidad y latencia, sin consumir tokens | Sí |

`stream()` y `list_models()` se mantienen en la interfaz aunque S2 no los use. Añadirlos después obligaría a cambiar todas las implementaciones existentes.

### 4. Tipos normalizados

**`CompletionRequest`:** `provider_model_id`, `messages` (rol y contenido), `max_output_tokens` (obligatorio y con un tope global), `temperature` (opcional), `timeout` y `request_id`.

**`CompletionResult`:** lo mínimo que devuelve cualquier proveedor.

| Campo | Notas |
|---|---|
| `content` | Texto generado |
| `inference_provider` | Qué sistema lo ejecutó |
| `provider_model_id` | El modelo que se usó realmente; un sistema de ejecución puede resolverlo a otra versión |
| `finish_reason` | `stop`, `length`, `content_filter` o `error` |
| `usage.input_tokens`, `usage.output_tokens`, `usage.source` | `source`: `reported` o `estimated`. Si el proveedor no informa, el valor es nulo; nunca se inventa. |
| `cost.amount`, `cost.currency`, `cost.source` | `source`: `reported` o `estimated_from_catalog` |
| `latency_ms` | Medida por nuestro backend |
| `provider_request_id` | Recomendado, para auditoría |

**`CompletionChunk`:** el fragmento de texto y, en el último, `finish_reason` y `usage`. Se define en S2 junto con `stream()`, aunque no se use todavía.

### 5. Errores tipados

Cada proveedor traduce sus errores a una jerarquía común. `ExecutionService` y la API reaccionan a estos tipos, nunca a los códigos HTTP de cada proveedor.

| Error | Causa típica | Respuesta de la API |
|---|---|---|
| `ProviderNotConfigured` | Falta la clave de API | 503 |
| `ProviderUnavailable` | Conexión rechazada, errores 5xx | 503 |
| `ProviderTimeout` | Se superó el timeout | 504 |
| `ProviderRateLimited` | Límite de peticiones (incluye `retry_after`) | 429 |
| `ProviderAuthError` | Clave inválida | 502, registrado como error de configuración |
| `ProviderBadRequest`, `ModelNotAvailable` | Modelo retirado, contexto excedido | 422 o 502 |

**En S2 no hay reintentos ni fallback automático.** Un error se devuelve tipado y no se prueba otro modelo ni otro proveedor. `ExecutionService` deja el punto de extensión para las cadenas de fallback de S3.

### 6. Operación: timeouts, health checks y capacidades

- **Timeouts:** explícitos y configurables por proveedor, de conexión (del orden de segundos) y de lectura (del orden de un minuto). Un cliente HTTP por proveedor, creado al arrancar la aplicación y cerrado al pararla.
- **Health checks:** `health()` comprueba disponibilidad y latencia sin generar tokens, para poder mostrar el estado de cada proveedor sin coste.
- **Capacidades:** `capabilities` declara qué ofrece cada proveedor. La API y las políticas futuras (privacidad en S3) consultan capacidades, no nombres de proveedor.

### 7. `ProviderRegistry` y configuración

- El registro se construye al arrancar a partir de la configuración y resuelve `inference_provider` → instancia.
- Un proveedor sin configurar se registra como **no configurado**. La aplicación arranca igual y solo `POST /api/v1/completions` responde 503 para ese proveedor.
- `COMPLETIONS_ENABLED` está **desactivado por defecto**, porque ejecutar modelos cuesta dinero. No se activa en entornos públicos sin autenticación o límites de uso.
- La clave de OpenRouter solo existe en el backend: nunca en variables `NEXT_PUBLIC_*`, en logs ni en el repositorio. Los logs registran metadatos, no prompts.

### 8. `OpenRouterProvider`

- Usa siempre un modelo explícito (`provider_model_id`). **No usa OpenRouter Auto:** la decisión es de la Decision Layer.
- OpenRouter y Ollama ofrecen APIs compatibles con la de OpenAI, así que la lógica HTTP común (petición, parseo y traducción de errores) vive en una base compartida. Cada proveedor define su URL, su autenticación, su endpoint de catálogo y sus capacidades.
- Las llamadas HTTP usan `httpx`, sin SDKs de cada fabricante: una sola dependencia y tests con transportes simulados, sin red.
- `list_models()` convertirá los precios de OpenRouter a USD por millón de tokens, la unidad de `model_prices`.
- Los endpoints y cabeceras exactos se verificarán en la documentación de OpenRouter al implementarlo. En S2 no se hacen llamadas reales.

### 9. `FakeProvider`

Proveedor determinista, sin red y sin coste, que devuelve respuestas predecibles con los tipos normalizados.

**Por qué `FakeProvider` y no `LocalProvider`:**

- **Evita confusión con Ollama.** En este proyecto, la ejecución local de modelos es Ollama. Un `LocalProvider` parecería otra forma de ejecutar modelos en la máquina del usuario.
- **No asocia "local" con privacidad.** "Local" ya significa algo concreto: los datos no salen de la máquina. Es la capacidad `local`, y la política de privacidad de S3 dependerá de ella. Un proveedor simulado no debe heredar esa connotación.
- **Representa claramente una simulación.** El nombre dice lo que es: no ejecuta ningún modelo.
- **Sirve para tests:** respuestas deterministas y sin red.
- **Sirve para CI:** sin claves ni secretos en el pipeline.
- **Sirve para demos:** una demo pública puede mostrar el flujo completo.
- **Evita costes:** ninguna ejecución genera gasto.

Una suite de conformidad común se ejecutará contra cada proveedor (`FakeProvider` y `OpenRouterProvider` con transporte simulado) para garantizar que todos cumplen la interfaz.

## Architectural Debt: mapeo transitorio `router_id → catalog_model`

Para respetar la regla de que el router no depende todavía del catálogo persistente, `ExecutionService` traduce el id de modelo del router a un modelo del catálogo mediante una tabla explícita, en un único módulo:

| `router_id` | Modelo del catálogo (`provider` / `model_key`) |
|---|---|
| `claude-sonnet` | `anthropic` / `claude-sonnet` |
| `gemini` | `google` / `gemini` |
| `gpt` | `openai` / `gpt-5` |
| `deepseek` | `deepseek` / `deepseek` |

- **Es deuda arquitectónica temporal.**
- **Está aprobada únicamente para S2.**
- **Se elimina en S2c,** cuando el router lea directamente el catálogo persistente.
- **El catálogo persistente será la fuente de verdad de los modelos.** La tabla no debe crecer con lógica propia ni usarse fuera de `ExecutionService`.
- Si un `router_id` no tiene correspondencia, `POST /api/v1/completions` devuelve un error tipado (`ModelNotAvailable`). La tabla nunca elige un modelo por su cuenta.

## Consequences

**Positivas**

- Añadir un sistema de ejecución consiste en implementar `InferenceProvider` y registrarlo, sin tocar el router ni `ExecutionService`.
- `POST /api/v1/route`, el Playground y el test de compatibilidad no cambian.
- Errores, uso y coste tienen la misma forma con cualquier proveedor, y cada coste lleva su moneda y su origen.
- Los tests, la CI y las demos no necesitan red, claves ni presupuesto.
- La aplicación arranca sin clave de API y sin base de datos; solo fallan los endpoints que las necesitan.
- `stream()` y `list_models()` ya forman parte del contrato, así que implementarlos no romperá la interfaz.

**Negativas**

- Más piezas que una llamada directa: interfaz, registro, servicio y tipos.
- El mapeo transitorio es deuda hasta S2c.
- Normalizar oculta particularidades de cada proveedor, salvo las que se expongan como capacidades.
- El primer endpoint que gasta dinero exige controles nuevos: feature flag, tope de tokens y modelos permitidos.
- Sin reintentos ni fallback, un fallo puntual del proveedor llega directamente al usuario hasta S3.

## Alternatives considered

### A. Router → OpenRouter directo

El router llama a OpenRouter justo después de decidir.

**Descartada:**

- Rompe el principio 1: la decisión y la ejecución quedarían acopladas.
- `POST /api/v1/route` dejaría de ser *decision-only*, rompiendo el Playground y el test de compatibilidad.
- Ollama y cualquier sistema futuro obligarían a modificar el router (principio 5).
- No se podría probar la decisión sin ejecutar, ni ejecutar sin decidir.

### B. Capa de abstracción de proveedores

**Elegida.** Cumple los siete principios: separa decisión y ejecución, mantiene `/route` intacto, normaliza tipos y errores, permite añadir proveedores sin tocar el router y deja los tests y las demos sin dependencia de proveedores de pago.

### C. Integraciones específicas por vendor

Una integración con el SDK de cada fabricante: OpenAI, Anthropic, Google, DeepSeek…

**Descartada:**

- Rompe el principio 2: trata a cada *vendor* como sistema de ejecución, cuando un mismo modelo puede ejecutarse a través de sistemas distintos.
- Multiplica dependencias, formatos de error y mantenimiento por cada fabricante.
- OpenRouter ya da acceso a todos ellos con una sola API compatible con la de OpenAI, y Ollama usa el mismo formato.

Una integración directa con un fabricante sigue siendo posible en el futuro como otra implementación de `InferenceProvider`, dentro de la opción B.

## Out of scope

No se implementa en S2:

- Llamadas reales a OpenRouter
- Streaming (`stream()` existe en la interfaz, sin implementar)
- Ollama
- Router → catálogo persistente
- Historial de uso
- Analítica
- Fallback automático
- Reintentos

## Future work

**S2 (este sprint):** interfaz, tipos, errores, `ProviderRegistry`, `ExecutionService`, `FakeProvider`, `OpenRouterProvider` probado con transporte simulado, migración del catálogo (`inference_provider`, `provider_model_id`) y `POST /api/v1/completions` detrás de `COMPLETIONS_ENABLED`.

**S2c** (reparto actualizado en ADR-0002):

- Router → catálogo persistente y eliminación del mapeo transitorio. Cambia `POST /api/v1/route`: el coste estimado pasa de € por 1.000 tokens a USD por millón, y `selected_model` pasa de `gpt` a `gpt-5`. Necesita su propio ADR y una actualización deliberada del test de compatibilidad.
- Llamadas reales a OpenRouter en entornos públicos, después de añadir autenticación o límites de uso.
- Streaming: implementar `stream()` y su transporte en la API.
- Historial de uso a partir de cada `CompletionResult`.
- Sincronización del catálogo con `list_models()`.

**S3:**

- `OllamaProvider` y el modelo de despliegue para llegar a una instancia local.
- Política de privacidad basada en la capacidad `local`.
- Reintentos y cadenas de fallback en `ExecutionService`.

**S6:** analítica construida sobre el historial de uso.

## Anexo: recomendación de licencia

**Estado:** recomendación. No modifica el archivo `LICENSE` actual. No es asesoramiento legal.

### Contexto

El repositorio se publica en GitHub como portfolio profesional. Los objetivos son:

- demostrar capacidad técnica y usarlo como currículum;
- comercializarlo en el futuro;
- ayudar a otras personas con el mismo problema;
- controlar la explotación comercial;
- **no permitir la reutilización libre del código.**

Hoy el repositorio tiene licencia **MIT**, añadida en S1.5 y publicada con la etiqueta `v0.6.1`. La etiqueta `v0.6.0` no incluía licencia.

### Opciones evaluadas

| | MIT | AGPL-3.0 | All Rights Reserved / Source Available Proprietary |
|---|---|---|---|
| Qué permite a terceros | Usar, modificar, redistribuir, vender y relicenciar el código sin pedir permiso | Usar, modificar, redistribuir y explotar comercialmente, siempre que publiquen el código de sus cambios, también si lo ofrecen como servicio en red | Ver el código. Según los términos de GitHub, también hacer fork dentro de la plataforma. Ningún otro uso sin permiso. |
| Código visible / portfolio | ✅ | ✅ | ✅ |
| Impide la reutilización libre | ❌ | ❌ | ✅ |
| Control de la explotación comercial | ❌ | ⚠️ Parcial | ✅ |
| Venta futura de licencias | ⚠️ Cualquiera puede competir con el mismo código | ✅ Con doble licencia | ✅ |

- **MIT: descartada.** Permite la reutilización irrestricta, incluida la explotación comercial por terceros.
- **AGPL-3.0: mejor que MIT, pero insuficiente.** Obliga a compartir los cambios, aunque sigue permitiendo que terceros usen, redistribuyan y exploten el código.
- **All Rights Reserved / Source Available Proprietary: recomendada.**

### Recomendación

Adoptar **All Rights Reserved / Source Available Proprietary** a partir de la próxima versión. Permite:

- mantener el código visible;
- conservar el portfolio público;
- vender licencias en el futuro;
- conservar el control total de la explotación comercial.

### Observaciones

1. **Las versiones ya publicadas bajo MIT seguirán siendo MIT para siempre.** Quien obtuvo el código de `v0.6.1` mantiene esos derechos. El cambio solo afecta a las versiones posteriores.
2. **Aplicar el cambio de forma coherente en un solo commit:** el archivo `LICENSE` (por un aviso de copyright con todos los derechos reservados), las secciones de licencia y el badge de `README.md` y `README.es.md`, y las menciones a MIT en `docs/PORTFOLIO.md` y `docs/PUBLISHING.md`.
3. **Ajustar la presentación pública:** el proyecto pasa a ser código visible como portfolio, no un proyecto abierto a reutilización ni a contribuciones externas.
4. **Si más adelante se quiere permitir ver y probar el código sin permitir competir con él**, existen licencias *source-available* con términos escritos, como la Business Source License o PolyForm Noncommercial.
5. **Antes de comercializar, consultar con un abogado:** el cambio de licencia y el tratamiento del código escrito con ayuda de asistentes de IA, cuya protección por derechos de autor no está igual de clara en todas las jurisdicciones.
