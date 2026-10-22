# AI Router Dashboard

### Un sistema que decide qué modelo de IA debe resolver cada tarea, y explica por qué.

**Rol:** diseño de producto, arquitectura y desarrollo full stack
**Stack:** Next.js · React · TypeScript · Tailwind · FastAPI · Python · PostgreSQL · Docker
**Estado:** prototipo funcional, en desarrollo activo
**Código:** [github.com/sofia-casado-sainz/ai-router-dashboard](https://github.com/sofia-casado-sainz/ai-router-dashboard)

<!-- Imagen de portada: captura del chat mostrando una decisión del router. -->

---

## El punto de partida

<!-- Ajusta esta sección con tu experiencia real. -->

Hubo un momento en el que tenía abiertos cuatro asistentes de IA a la vez y ningún criterio para decidir a cuál preguntar qué. Para un correo rápido usaba el mismo modelo que para diseñar un sistema, y pagaba lo mismo por las dos cosas. Otras veces hacía lo contrario: probaba con el más barato, la respuesta no servía y acababa repitiéndolo todo con otro.

Me di cuenta de que no era un problema de herramientas, sino de decisión. Cada modelo tiene un precio, una ventana de contexto y unos puntos fuertes distintos. Algunos se pueden ejecutar en local, gratis y sin que los datos salgan del ordenador. Elegir bien depende de la tarea, del presupuesto y de lo sensible que sea la información. Esa elección se puede automatizar.

## El reto

Quería construir algo que, a partir de un simple texto, respondiera a tres preguntas:

1. **¿Qué tan difícil es esta tarea?**
2. **¿Qué modelos pueden resolverla de forma aceptable** dentro de mis límites de coste y privacidad?
3. **De esos, ¿cuál me conviene más?** Y, sobre todo, ¿puedo explicar por qué?

Ese último punto acabó guiando el diseño. Un router que acierta pero no explica sus decisiones es una caja negra, y nadie confía su presupuesto a una caja negra. Por eso cada respuesta del sistema muestra el modelo elegido, la complejidad estimada, el coste previsto y el motivo.

## Cómo lo abordé

**Primero, que funcionara de extremo a extremo.** Antes de pensar en algoritmos sofisticados, construí el recorrido completo: una interfaz de chat en Next.js, una API en FastAPI y un primer motor de decisión basado en reglas. Era deliberadamente simple. Quería validar la experiencia (escribir una tarea y ver una decisión razonada) antes de invertir en la parte difícil.

**Después, auditar antes de crecer.** Con el prototipo en marcha hice una auditoría técnica de mi propio código. Encontré cosas que no escalaban: el catálogo de modelos estaba duplicado entre frontend y backend, y bastaba un modelo nuevo para romper la interfaz. Los tipos se copiaban a mano entre los dos lados. La configuración estaba dispersa. Nada de esto se veía desde fuera, pero cada uno era una deuda que crecería con cada funcionalidad.

**Luego, fundaciones.** Dediqué un sprint completo a no añadir nada visible: configuración centralizada, logs estructurados, una API versionada, Docker para levantar todo el entorno con un comando y un contrato OpenAPI entre frontend y backend, protegido por un test. Es el tipo de trabajo que no luce en una demo, pero es lo que permite que el proyecto crezca sin miedo a romperlo.

## Decisiones que me hicieron pensar

**¿Python o TypeScript para el backend?** Usar un solo lenguaje habría sido más cómodo. Elegí Python porque el ecosistema de IA (clasificadores, embeddings, SDKs) vive ahí, y el motor de enrutado es el corazón del producto. A cambio asumí el coste de mantener dos lenguajes sincronizados, y resolví ese problema de forma explícita con un contrato generado desde el backend.

**¿Integrar cada proveedor o usar un intermediario?** OpenRouter da acceso a GPT, Claude, Gemini y DeepSeek con una única API y precios actualizados. Me ahorra cinco integraciones, pero también me obliga a tener muy claro dónde aporta valor mi proyecto, porque OpenRouter ya tiene su propio enrutado automático. Mi respuesta: lo que lo diferencia son las políticas por equipo, los presupuestos, la privacidad y que cada decisión se pueda explicar.

**Lo local no es solo "otro proveedor".** Integrar modelos locales con Ollama parecía trivial, porque usa la misma API. Pero un servicio en la nube no puede llegar al ordenador del usuario. Esa diferencia cambia por completo cómo se despliega el producto, y me alegro de haberla detectado en la fase de diseño y no después de prometerla.

## Dónde está hoy

El flujo completo funciona: escribes *"Diseña una arquitectura cloud escalable"* y el sistema responde que lo resolvería Claude Sonnet, con una complejidad de 8 sobre 10, un coste estimado de unos 0,018 € y el motivo de la elección.

Soy transparente con lo que aún no es real: la decisión se toma con reglas, los precios son simulados y el dashboard muestra datos de ejemplo. Las siguientes fases conectan la base de datos, las llamadas reales a los modelos, la integración local con Ollama y un motor de puntuación que equilibre calidad, coste y latencia.

## Lo que me llevo

- **Lo difícil de un router de IA no es llamar a los modelos, es entender la tarea.** Mi primer motor me enseñó sus límites enseguida: con reglas de palabras clave, el orden de las reglas pesa más que el contenido del texto.
- **Una métrica sin referencia no es una métrica.** Mostrar "ahorro generado" exige definir ahorro *respecto a qué*. Si no, es un número bonito y vacío.
- **Medir antes de optimizar.** Sin un conjunto de pruebas propio no puedo demostrar que el sistema elige bien, así que construir ese conjunto va antes que mejorar el algoritmo.
- **Invertir en fundaciones pronto es barato.** Ordenar configuración, logs y contratos con dos endpoints me llevó un sprint. Con veinte habría sido una migración dolorosa.
- **Diseñar para lo desconocido.** La interfaz ya no asume qué modelos existen. Si mañana aparece uno nuevo, la aplicación lo muestra en lugar de romperse.

## Siguientes pasos

Persistencia y precios reales → respuestas reales vía OpenRouter → modelos locales con Ollama → equipos y presupuestos → un motor de decisión medido con datos propios.

---

<!-- Enlaces de contacto para tu portfolio -->
**¿Hablamos?** [GitHub](https://github.com/sofia-casado-sainz) · LinkedIn · Email
