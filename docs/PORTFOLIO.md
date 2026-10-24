# AI Router

Un sistema que decide qué modelo de IA debería resolver cada tarea y explica por qué.

- **Proyecto:** personal. Producto, arquitectura y desarrollo full stack.
- **Perfil:** AI Engineer orientada a agentes de IA, automatización y sistemas de decisión.
- **Stack:** Next.js · React · TypeScript · Tailwind · FastAPI · Python · PostgreSQL · SQLAlchemy (async) · Alembic · Docker
- **Estado:** prototipo funcional (v0.6.0), en desarrollo.
- **Código:** [github.com/sofia-casado-sainz/ai-router-dashboard](https://github.com/sofia-casado-sainz/ai-router-dashboard)

## Qué es

AI Router recibe la descripción de una tarea y decide qué modelo de IA usaría para resolverla. Cada decisión muestra el modelo elegido, la complejidad estimada, el coste estimado y el motivo. Hoy decide con reglas de palabras clave; el objetivo es que equilibre coste, calidad, latencia y privacidad.

## Por qué existe

Quería aprovechar mejor las IAs que uso para estudiar, programar y construir proyectos.

El ecosistema cambia constantemente. Aparecen modelos nuevos. Cambian los precios. Cambian las capacidades.

AI Router nace primero como una herramienta para centralizar esa decisión para mí misma y después como una plataforma que pueda ayudar a otras personas con el mismo problema.

## Qué hace hoy

- **Playground:** describes una tarea y ves la decisión del router (modelo, proveedor, complejidad, coste estimado, motivo y palabras clave detectadas). No llama al modelo elegido ni genera respuestas.
- **Models:** catálogo persistente en PostgreSQL con proveedor, ventana de contexto, estado y precio vigente de cada modelo. Los precios son de ejemplo.
- **Dashboard:** diseño de las métricas de consumo y ahorro, con datos de ejemplo señalizados en la propia pantalla.
- **API:** `POST /api/v1/route` y `GET /api/v1/models`, versionada y documentada con OpenAPI.

Las limitaciones están documentadas en el [README](../README.es.md#limitaciones-conocidas).

## Cómo se ha construido

El proyecto avanza por sprints, cada uno con un objetivo cerrado y criterios de aceptación. Entre sprints hice auditorías técnicas que marcaron el siguiente paso.

- **Prototipo:** recorrido completo de extremo a extremo con una interfaz en Next.js, una API en FastAPI y un primer motor de decisión basado en reglas.
- **S0 · Fundaciones:** configuración centralizada, logs estructurados en JSON, API versionada en `/api/v1`, Docker Compose y un contrato OpenAPI comprobado por un test. El catálogo de modelos, que estaba duplicado en el frontend, pasó a vivir solo en el backend.
- **S0.5 · Producto:** la interfaz de chat se convirtió en un Playground, la navegación se limitó a lo implementado y los datos de ejemplo quedaron señalizados. También se corrigieron problemas que solo aparecían fuera de mi máquina: el typecheck en un clon limpio, los tests afectados por plugins de pytest del sistema y una redirección permanente difícil de deshacer.
- **S1 · Persistencia:** catálogo de modelos en PostgreSQL con SQLAlchemy asíncrono, migraciones con Alembic, seed idempotente, `GET /api/v1/models` y la página Models. Validado con Docker y en el navegador, incluidos los estados de carga, vacío y error.
- **S1.5 · Portfolio y open source:** documentación bilingüe, licencia MIT y preparación de CI y releases.

## Decisiones de arquitectura

**Backend en Python con un contrato explícito.** Elegí FastAPI porque la mayor parte de las herramientas de IA (SDKs, embeddings, clasificadores) están en Python. Tener dos lenguajes obliga a mantenerlos sincronizados, así que el esquema OpenAPI se exporta a `contracts/openapi.json` y un test falla si deja de coincidir con la API.

**Un Playground en lugar de un chat.** La primera interfaz tenía forma de chat, pero el producto todavía no genera respuestas. La convertí en un Playground que presenta la decisión del router como resultado principal, para que la interfaz no prometa algo que aún no existe.

**Catálogo persistente sin tocar el router.** En S1 la restricción principal fue no cambiar el comportamiento del router. El catálogo se separó en capas (`api`, `services`, `repositories`, `domain`, `database`) y el router siguió usando su catálogo interno. Un test comprueba que `POST /api/v1/route` devuelve exactamente lo mismo que antes. El coste de esta decisión es que hoy conviven varias fuentes de datos de modelos; unificarlas es el primer objetivo de S2.

**OpenRouter y Ollama como plan de proveedores.** OpenRouter da acceso a muchos modelos comerciales con una sola integración, y Ollama a modelos locales con la misma API. Lo local plantea un problema de despliegue: un servicio en la nube no puede llegar al ordenador del usuario, así que hay que diseñar ese despliegue antes de ofrecer la funcionalidad.

## Uso de IA

Utilicé Claude Code, GitHub Copilot y otros asistentes para acelerar la implementación, realizar auditorías técnicas y explorar alternativas de diseño.

La definición del producto, las decisiones de arquitectura, el roadmap, las restricciones técnicas y la validación de cada sprint fueron responsabilidad mía.

La IA me permitió delegar parte de la escritura del código mientras mantenía el control sobre el diseño y la comprensión del sistema.

## Qué he aprendido

- **Las reglas por palabras clave tienen un límite claro.** Con la primera regla que coincide como criterio, el orden de las reglas decide en los casos ambiguos. Mejorar el router exige clasificar la tarea y medir los resultados con un conjunto de pruebas propio.
- **Una métrica de ahorro necesita una línea base visible.** Sin decir respecto a qué se ahorra, el número no significa nada.
- **Un contrato entre frontend y backend tiene que estar comprobado.** Exportar el esquema y validarlo en un test evita que se desactualice sin que nadie lo note.
- **Validar fuera de mi máquina encuentra errores reales.** Un clon limpio, Docker y el navegador detectaron fallos que los tests locales no veían.

Los problemas concretos, con su diagnóstico y su solución, están en el [registro de incidencias](INCIDENTS.md).

## Próximos pasos

- **S2:** conectar el router al catálogo persistente, integrar OpenRouter para obtener respuestas reales, registrar el uso y el coste reales, y generar los tipos del frontend desde OpenAPI.
- **Más adelante:** modelos locales con Ollama, equipos y presupuestos, y un motor de decisión que equilibre coste, calidad y latencia, evaluado con un dataset propio.

## Contacto

- **GitHub:** [@sofia-casado-sainz](https://github.com/sofia-casado-sainz)
- **LinkedIn:** [sofia-casado-sainz](https://www.linkedin.com/in/sofia-casado-sainz-4094a028a)
