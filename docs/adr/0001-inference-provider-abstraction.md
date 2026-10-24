# ADR 0001: Inference Provider Abstraction

- **Fecha:** 2026-10-24
- **Sprint:** S2 · OpenRouter Foundation
- **Decide:** Sofía Casado Sainz

## Status

**Aceptado.** Este ADR define la arquitectura. Nada de lo descrito está implementado todavía.

El anexo sobre licencia es una **propuesta** independiente de la arquitectura de proveedores; si se aprueba, debería pasar a su propio ADR.

## Context

**Estado actual (después de S1):**

- `POST /api/v1/route` decide qué modelo usar y lo explica, pero no ejecuta nada. El Playground depende de esa respuesta, y `tests/test_route_compat.py` comprueba que no cambia.
- El router decide con reglas sobre su catálogo interno (`router/catalog.py`: `gpt`, `claude-sonnet`, `gemini`, `deepseek`, con precios simulados en € por 1.000 tokens).
- El catálogo persistente de S1 (`models`, `model_prices`) guarda modelos de ejemplo con precios en USD por millón de tokens. En esa tabla, la columna `provider` identifica al **vendor** del modelo: `openai`, `anthropic`, `google`, `deepseek`, `ollama`.
- `ModelCatalogService` declara `sync_openrouter_models()` y `sync_ollama_models()` sin implementar.

**Qué cambia en S2:** el sistema tiene que poder ejecutar el modelo elegido y devolver una respuesta real. El primer proveedor será OpenRouter; después vendrán Ollama (S3) y otros.

**Restricciones:**

1. El router sigue siendo *decision-only*: `POST /api/v1/route` no cambia.
2. El Playground funciona igual.
3. El router todavía no depende del catálogo persistente.
4. No se usa el enrutado automático de OpenRouter (OpenRouter Auto): las decisiones las toma este sistema.
5. Todos los proveedores devuelven los mismos tipos normalizados.
6. Añadir OpenRouter, Ollama u otros proveedores no puede obligar a cambiar el router.

**Lecciones previas que condicionan el diseño** (ver `docs/INCIDENTS.md`):

- Una configuración incorrecta no debe impedir que arranque toda la aplicación.
- Toda llamada de red necesita un timeout explícito; sin él, un servicio que no responde bloquea la petición durante decenas de segundos.
- Cada coste debe llevar su moneda: hoy conviven € y USD.

## Decision

### 1. Decidir y ejecutar son operaciones separadas

- `POST /api/v1/route` sigue igual: solo decide.
- `POST /api/v1/completions` (nuevo) decide **y** ejecuta. Lo orquesta `ExecutionService`, que no conoce HTTP ni proveedores concretos.

```text
POST /api/v1/completions
  → ExecutionService
      1. Router (sin cambios)               → decisión: id de modelo del router
      2. Resolución de modelo (transitoria) → modelo del catálogo: inference_provider + provider_model_id
      3. ProviderRegistry                   → InferenceProvider
      4. InferenceProvider.complete()       → CompletionResult
  → respuesta: decisión (misma forma que /route) + resultado
```

La resolución del paso 2 es una tabla explícita, en un único módulo, que traduce los ids del router (`gpt`) a modelos del catálogo (`openai` / `gpt-5`). Así el router no depende del catálogo y `/route` no cambia. Esa tabla desaparece cuando el router lea directamente el catálogo (S2b).

### 2. `inference_provider`: un concepto distinto de `provider`

- **`provider`** (existente): quién crea el modelo. Por ejemplo, `anthropic`.
- **`inference_provider`** (nuevo): quién lo ejecuta para nosotros. Por ejemplo, `openrouter`, `ollama` o `fake`.

El catálogo añadirá `inference_provider` y `provider_model_id` (el identificador del modelo en ese proveedor) mediante una migración nueva. `GET /api/v1/models` solo ganará campos.

### 3. Interfaz `InferenceProvider`

Un protocolo asíncrono que implementa cada proveedor:

| Miembro | Responsabilidad |
|---|---|
| `key` | Identificador estable: `"openrouter"`, `"ollama"`, `"fake"`. Coincide con `inference_provider` en el catálogo. |
| `capabilities` | `streaming`, `local` (los datos no salen de la máquina), `reports_cost`, `lists_models` |
| `complete(CompletionRequest) → CompletionResult` | Una respuesta completa. Es lo único que necesita S2a. |
| `stream(CompletionRequest) → CompletionChunk…` | Respuesta por fragmentos. Declarado en la interfaz, implementado más adelante. |
| `list_models()` | Catálogo del proveedor, base de `sync_openrouter_models()` y `sync_ollama_models()`. |
| `health()` | Disponibilidad y latencia **sin consumir tokens**. |

### 4. Tipos normalizados

**`CompletionRequest`:** `provider_model_id`, `messages` (rol y contenido), `max_output_tokens` (obligatorio y con un tope global), `temperature` (opcional), `timeout` y `request_id`.

**`CompletionResult`:** lo mínimo que debe devolver cualquier proveedor.

| Campo | Notas |
|---|---|
| `content` | Texto generado |
| `inference_provider` | Qué proveedor lo ejecutó |
| `provider_model_id` | El modelo que se usó realmente; un proveedor puede resolverlo a otra versión |
| `finish_reason` | `stop`, `length`, `content_filter` o `error` |
| `usage.input_tokens`, `usage.output_tokens`, `usage.source` | `source` es `reported` o `estimated`; si el proveedor no informa, el valor es nulo, nunca inventado |
| `cost.amount`, `cost.currency`, `cost.source` | `source` es `reported` o `estimated_from_catalog` |
| `latency_ms` | Medida por nuestro backend |
| `provider_request_id` | Recomendado, para auditoría |

**`CompletionChunk`:** el fragmento de texto y, en el último, `finish_reason` y `usage`.

### 5. Errores tipados

Los proveedores traducen sus errores a una jerarquía común. `ExecutionService` y la API reaccionan a estos tipos, nunca a los códigos HTTP de cada proveedor.

| Error | Causa típica | Respuesta de la API |
|---|---|---|
| `ProviderNotConfigured` | Falta la clave de API | 503 |
| `ProviderUnavailable` | Conexión rechazada, errores 5xx | 503 |
| `ProviderTimeout` | Se superó el timeout | 504 |
| `ProviderRateLimited` | Límite de peticiones (incluye `retry_after`) | 429 |
| `ProviderAuthError` | Clave inválida | 502, registrado como error de configuración |
| `ProviderBadRequest`, `ModelNotAvailable` | Modelo retirado, contexto excedido | 422 o 502 |

En S2 no hay reintentos ni fallback a otro modelo: el error se devuelve tipado. El punto de extensión para las cadenas de fallback de S3 queda en `ExecutionService`.

### 6. Timeouts y health checks

- Cada proveedor tiene timeouts explícitos y configurables: de conexión (del orden de segundos) y de lectura (del orden de un minuto).
- Un cliente HTTP por proveedor, creado al arrancar la aplicación y cerrado al pararla.
- `health()` no genera tokens: comprueba disponibilidad y latencia, para poder mostrar el estado de cada proveedor sin coste.

### 7. `ProviderRegistry` y configuración

- El registro se construye al arrancar a partir de la configuración y resuelve `inference_provider` → instancia.
- Un proveedor sin configurar (por ejemplo, sin clave) se registra como **no configurado**. La aplicación arranca igual y solo `POST /api/v1/completions` responde 503 para ese proveedor.
- `COMPLETIONS_ENABLED` está **desactivado por defecto**. Ejecutar modelos cuesta dinero, y el endpoint no se expone hasta que existan autenticación o límites de uso.
- La clave de OpenRouter solo existe en el backend. Nunca va en variables `NEXT_PUBLIC_*`, ni en logs, ni en el repositorio. Los logs registran metadatos, no prompts.

### 8. `OpenRouterProvider`

- Usa siempre un modelo explícito (`provider_model_id`). No usa OpenRouter Auto.
- OpenRouter y Ollama ofrecen APIs compatibles con la de OpenAI, así que la lógica HTTP común (petición, parseo y traducción de errores) vive en una base compartida. Cada proveedor define su URL, su autenticación, su endpoint de catálogo y sus capacidades.
- Las llamadas HTTP usan `httpx`, sin SDKs de cada fabricante: una sola dependencia y tests con transportes simulados, sin red.
- `list_models()` convertirá los precios de OpenRouter a USD por millón de tokens, la unidad de `model_prices`.
- Los endpoints y cabeceras exactos se verificarán en la documentación de OpenRouter al implementarlo.

### 9. `FakeProvider`

Un proveedor determinista, sin red y sin coste, que devuelve respuestas predecibles con tipos normalizados. Sirve para:

- tests y CI, sin claves ni llamadas externas;
- desarrollo local sin cuenta en OpenRouter;
- una demo pública que no gaste dinero.

Una suite de conformidad común se ejecutará contra cada proveedor (`FakeProvider` y `OpenRouterProvider` con transporte simulado) para garantizar que todos cumplen la interfaz.

**Por qué `FakeProvider` y no `LocalProvider`:** en este proyecto, "local" ya significa algo concreto: modelos que se ejecutan en la máquina del usuario (Ollama) y que no envían datos fuera. Esa propiedad es la `capability` `local`, y la política de privacidad de S3 dependerá de ella. Un proveedor llamado `LocalProvider` que no ejecuta ningún modelo confundiría dos ideas distintas: la privacidad de lo local y la simulación. `FakeProvider` dice exactamente lo que es: una implementación simulada.

## Consequences

**Positivas**

- Añadir un proveedor consiste en implementar `InferenceProvider` y registrarlo, sin tocar el router ni `ExecutionService`.
- `/route`, el Playground y el test de compatibilidad no cambian.
- Los errores, el uso y el coste tienen la misma forma con cualquier proveedor, y cada coste lleva su moneda y su origen.
- Los tests no necesitan red ni claves.
- La aplicación sigue arrancando sin clave de API y sin base de datos; solo fallan los endpoints que las necesitan.

**Negativas**

- Más piezas que una llamada directa: interfaz, registro, servicio y tipos.
- La tabla de resolución entre el router y el catálogo es deuda temporal hasta S2b.
- Normalizar obliga a perder detalles específicos de cada proveedor, salvo los que se añadan como capacidades.
- El primer endpoint que gasta dinero exige controles nuevos: feature flag, tope de tokens y modelos permitidos.

## Alternatives considered

### A. Router → OpenRouter directo

El router llama a OpenRouter justo después de decidir.

**Descartada:**

- El router dejaría de ser *decision-only* y `POST /api/v1/route` cambiaría, rompiendo el Playground y el test de compatibilidad.
- Ollama y cualquier proveedor futuro obligarían a modificar el router.
- Mezclaría decisión y ejecución, y no se podría probar una sin la otra.

### B. Capa de abstracción de proveedores

**Elegida**, por los motivos de la sección *Decision*.

### C. Integraciones específicas por vendor

Una integración con el SDK de cada fabricante: OpenAI, Anthropic, Google, DeepSeek…

**Descartada:**

- Multiplica dependencias, formatos de error y mantenimiento por cada fabricante.
- OpenRouter ya da acceso a todos ellos con una sola API compatible con la de OpenAI, y Ollama usa el mismo formato.
- Confunde *vendor* con *inference provider*: el mismo modelo puede ejecutarse a través de proveedores distintos.

Si en el futuro hace falta una integración directa con un fabricante, cabe dentro de la opción B como otra implementación de `InferenceProvider`.

## Future work

**S2a (este sprint):** implementar lo descrito en *Decision*: interfaz, tipos, errores, registro, `FakeProvider`, `OpenRouterProvider` y `POST /api/v1/completions` detrás de `COMPLETIONS_ENABLED`, con migración del catálogo y tests sin red.

**Fuera del alcance de este ADR:**

- **Router → catálogo persistente (S2b).** Cambia `POST /api/v1/route`: el coste estimado pasa de € por 1.000 tokens a USD por millón, y `selected_model` pasa de `gpt` a `gpt-5`. Necesita su propio ADR y una actualización deliberada del test de compatibilidad.
- **Llamadas reales a OpenRouter** en entornos públicos, después de añadir autenticación o límites de uso.
- **Streaming:** implementar `stream()` y su transporte en la API.
- **Historial de uso:** persistir cada `CompletionResult` (tokens, coste, latencia). `ExecutionService` deja preparado el punto de registro.
- **Sincronización del catálogo** con `list_models()`.
- **Ollama (S3):** `OllamaProvider`, la política de privacidad basada en la capacidad `local`, las cadenas de fallback y el modelo de despliegue para llegar a una instancia local.
- **Analítica (S6):** construida sobre el historial de uso.

## Anexo: recomendación de licencia

**Estado:** propuesta. No modifica el archivo `LICENSE` actual. No es asesoramiento legal.

### Contexto

- El repositorio es público en GitHub como portfolio.
- La intención es comercializar el producto en el futuro.
- No se quiere permitir la reutilización libre del código.
- Hoy el repositorio tiene licencia **MIT**, añadida en S1.5 y publicada con la etiqueta `v0.6.1`. La etiqueta `v0.6.0` no incluía licencia.

### Opciones

| | MIT (actual) | AGPL-3.0 | Todos los derechos reservados |
|---|---|---|---|
| Qué permite a terceros | Usar, modificar, vender y relicenciar el código sin pedir permiso | Usar y modificar, incluso con fines comerciales, si publican sus cambios, también cuando lo ofrecen como servicio en red | Ver el código en GitHub; según los términos de GitHub, también hacer fork dentro de la plataforma. Nada más sin permiso. |
| Encaja con "no permitir reutilización libre" | ❌ | ⚠️ Solo en parte: la reutilización sigue permitida si se comparte el código | ✅ |
| Comercialización futura | Cualquiera puede competir con el mismo código | Posible con doble licencia (AGPL + licencia comercial), porque la autora tiene los derechos de su código | Sin restricciones para la autora |
| Portfolio | ✅ | ✅ | ✅ El código sigue siendo visible |
| Contribuciones externas | Las facilita | Las permite con más fricción | Prácticamente las impide |

### Recomendación

**Todos los derechos reservados** a partir de la próxima versión. Es la única de las tres opciones que cumple el objetivo de no permitir la reutilización, y no impide usar el repositorio como portfolio.

A tener en cuenta:

1. **Lo publicado con MIT no se puede retirar.** Quien obtuvo el código de `v0.6.1` lo tiene con licencia MIT para siempre. El cambio solo afecta a las versiones posteriores.
2. **Hay que actualizar todo a la vez:** el archivo `LICENSE` (por un aviso de copyright con todos los derechos reservados), las secciones de licencia y el badge de `README.md` y `README.es.md`, y las menciones a MIT en `docs/PORTFOLIO.md` y `docs/PUBLISHING.md`.
3. **El objetivo "open source" de S1.5 deja de aplicar.** Habría que ajustar cómo se presenta el proyecto: código visible como portfolio, no proyecto abierto a contribuciones.
4. **Si más adelante se quiere permitir ver y probar el código sin permitir competir con él**, existen licencias *source-available* (por ejemplo, Business Source License o PolyForm Noncommercial). Pueden encajar en un modelo comercial, pero conviene decidirlo con asesoramiento.
5. **Antes de comercializar, consultar con un abogado:** el cambio de licencia y el tratamiento del código escrito con ayuda de asistentes de IA, cuya protección por derechos de autor no está igual de clara en todas las jurisdicciones.
