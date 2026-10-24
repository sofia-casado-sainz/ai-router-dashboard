# ADR 0003: Exposure Gate for Real Inference Providers

- **Fecha:** 2026-10-24
- **Sprint:** S2b · OpenRouter Foundation
- **Decide:** Sofía Casado Sainz
- **Relacionado:** [ADR-0001](0001-inference-provider-abstraction.md), [ADR-0002](0002-execution-wiring-and-provider-operations.md)

## Status

**Aceptado.** Se implementa en S2b-2, junto con `OpenRouterProvider`.

## Context

`POST /api/v1/completions` ejecuta modelos. Con `FakeProvider` no tiene coste. Con un proveedor real, como OpenRouter, cada petición gasta dinero de la cuenta asociada a la clave de API.

Hoy el endpoint:

- no tiene autenticación;
- no limita el número de peticiones;
- acepta cualquier modelo que el router elija;
- permite pedir hasta 8.192 tokens de salida por petición.

La única protección es `COMPLETIONS_ENABLED`, desactivado por defecto. No basta para activar un proveedor real.

## Decision

### Proveedor real

Un proveedor es **real** si ejecuta modelos reales, como `OpenRouterProvider` u `OllamaProvider`. No lo son `FakeProvider` ni la sustitución simulada de ADR-0002.

### Interlock

Si hay un proveedor real registrado y `COMPLETIONS_ENABLED=true`, `POST /api/v1/completions` responde **503** con `code="exposure_gate_not_satisfied"` mientras falte cualquiera de estos requisitos:

1. **Autenticación.**
   - `COMPLETIONS_API_KEYS` contiene al menos una clave, guardada como hash SHA-256 y comparada en tiempo constante.
   - Las peticiones envían `Authorization: Bearer <clave>`. Si falta o no es válida, la respuesta es **401** (`unauthorized`).
2. **Lista de modelos permitidos.**
   - `COMPLETIONS_ALLOWED_MODELS` contiene modelos del catálogo (`provider/model_key`).
   - Si el modelo decidido no está en la lista, la respuesta es **403** (`model_not_allowed`).
   - **Una lista vacía no permite ningún modelo.**
3. **Topes por petición.**
   - `COMPLETIONS_MAX_OUTPUT_TOKENS`, por defecto 1.024, por debajo del límite de dominio de 8.192.
   - Una longitud máxima de prompt más estricta que la de `/route`.
   - Superarlos devuelve **422**.
4. **Límite de peticiones.**
   - En memoria, por clave y global.
   - Superarlo devuelve **429** (`rate_limited`) con `Retry-After`.

El interlock comprueba la configuración: si un requisito falta, el endpoint no ejecuta nada, aunque la petición sea correcta.

### Secretos

- La clave de OpenRouter es un `SecretStr`.
- Nunca aparece en logs, respuestas, el esquema OpenAPI, variables `NEXT_PUBLIC_*` ni en el repositorio.
- Un test lo comprueba.

### Fuera de este ADR

- **Presupuestos y alertas de gasto (S6).** Necesitan el historial de uso.
- **Claves por equipo y organizaciones (S4).**
- **Almacenamiento compartido para el límite de peticiones (S4).** El límite en memoria funciona por proceso; hasta entonces, el despliegue con un proveedor real es de una sola instancia.

## Consequences

**Positivas**

- No se puede exponer un proveedor de pago por olvidar una variable: la configuración incompleta bloquea la ejecución.
- Los límites cubren los dos riesgos principales: uso no autorizado y gasto descontrolado por petición.
- Todo el control es configuración del backend; no depende del frontend.

**Negativas**

- El límite en memoria no sirve con varias instancias.
- Las claves de API son globales, no por equipo, hasta S4.
- Sin presupuestos (S6), el gasto total solo está acotado por el límite de peticiones y los topes por petición.

## Alternatives considered

- **Confiar solo en `COMPLETIONS_ENABLED`:** descartada. Un único interruptor no distingue entre una demo con `FakeProvider` y un proveedor que gasta dinero.
- **Delegar la autenticación en un proxy inverso:** descartada como requisito único. Depende del despliegue y no se puede comprobar desde la aplicación.
- **Implementar ya equipos, claves por organización y presupuestos:** descartada. Es el alcance de S4 y S6; aquí basta con el mínimo que impide exponer un proveedor real sin protección.
