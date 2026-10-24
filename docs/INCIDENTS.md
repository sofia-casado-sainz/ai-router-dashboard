# Incidents and Engineering Notes

Registro de problemas reales encontrados durante el desarrollo (S0 a S1.5): qué pasó, cómo encontré la causa, qué cambié y qué dejó en el proyecto. Las investigaciones las hice con ayuda de Claude Code (ver [Cómo he usado la IA](../README.es.md#cómo-he-usado-la-ia)). Los mensajes de error y los comandos son los que aparecieron en cada caso.

## 1. `tsc` fallaba en un clon limpio por `LayoutProps`

### Contexto

Al cerrar S0.5 quise comprobar que cada commit compilaba por sí solo. Creé un clon temporal del repositorio, apliqué los commits uno a uno y ejecuté `tsc --noEmit` en cada uno.

### Síntomas

El typecheck falló en los cuatro commits, incluido el último, que era idéntico a mi copia de trabajo, donde sí pasaba:

```text
src/app/layout.tsx(24,50): error TS2304: Cannot find name 'LayoutProps'.
```

`src/app/layout.tsx` no había cambiado desde S0, así que no era un fallo introducido por esos commits.

### Diagnóstico

`LayoutProps` es un tipo global que genera Next.js a partir de la estructura de `src/app`. Se escribe en `.next/types/` y `next-env.d.ts`, que están en `.gitignore`. En mi máquina existían porque ya había ejecutado `next build` o `next dev`; en un clon limpio no. `tsc` por sí solo no los genera.

Next.js 16.4.2 incluye `next typegen`, que genera esos tipos sin hacer un build. Lo comprobé en el clon: después de `next typegen`, `tsc --noEmit` pasaba.

### Solución

- Añadí el script `"typecheck": "next typegen && tsc --noEmit"` en `frontend/package.json`.
- Lo validé en dos clones nuevos, cada uno con su propio `npm ci`, ejecutando `lint`, `typecheck` y `build` en órdenes distintos. Los tres pasaron en ambos.

Al probar casos límite apareció otro problema. Si se borra o renombra una ruta después de haber usado `next dev`, tanto `typecheck` como `build` fallan con errores en `.next/dev/types/validator.ts`: `next typegen` regenera `.next/types`, pero no los tipos que guarda el servidor de desarrollo en `.next/dev`. Probé un `tsconfig` separado para el typecheck que ignorase `.next/dev` y lo descarté: `typecheck` pasaba, pero `next build` seguía fallando, y el typecheck dejaba de anticipar lo que hace el build. Lo documenté en `docs/DEVELOPMENT.md` con la solución que sí funciona: borrar `frontend/.next/dev`.

### Aprendizaje

- El typecheck del proyecto es `npm run typecheck`, nunca `tsc` a secas. La CI prevista en `docs/PUBLISHING.md` usa ese script.
- Antes de dar por buena una validación, la repito en un clon limpio: mi copia de trabajo arrastra artefactos que ocultan errores.

## 2. pytest cargaba plugins de ROS 2 instalados en el sistema

### Contexto

En mi máquina tengo ROS 2 Jazzy. Al cargar su entorno (`source /opt/ros/jazzy/setup.bash`) queda exportado:

```text
PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages
```

### Síntomas

`pytest` fallaba antes de ejecutar ningún test, con una traza que terminaba en paquetes de ROS:

```text
File "/opt/ros/jazzy/lib/python3.12/site-packages/launch/frontend/parse_substitution.py", line 23, in <module>
    from lark import Lark
ModuleNotFoundError: No module named 'lark'
```

Con `PYTHONPATH= pytest` o `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest` los 22 tests pasaban. La guía de desarrollo recomendaba el primer apaño.

### Diagnóstico

Pytest carga automáticamente los plugins que encuentra registrados en `sys.path`. Listando esos registros con el `PYTHONPATH` de ROS activo aparecían siete plugins de `/opt/ros/jazzy` (`launch_testing`, `launch_ros` y cinco `ament_*`) y uno del propio entorno virtual (`anyio`). `launch_testing` importa `launch`, que necesita `lark`, y `lark` no está en el entorno virtual del proyecto.

También comprobé que la variable no afectaba a la aplicación: con la carga automática desactivada no se importaba ningún módulo desde `/opt/ros`.

Para no depender de una variable de entorno, revisé el código de pytest 9.1.1: las opciones de `addopts` de la configuración se leen antes de la carga automática de plugins, así que se puede desactivar desde `pyproject.toml`. La opción `--disable-plugin-autoload` no existe en versiones anteriores: con pytest 8.3.5 falla con `unrecognized arguments`; con 8.4.0 funciona.

### Solución

En `backend/pyproject.toml`:

- `addopts = ["--disable-plugin-autoload"]` en `[tool.pytest.ini_options]`.
- Versión mínima `pytest>=8.4` en las dependencias de desarrollo.

Validé `pytest`, `python -m pytest`, la ejecución desde la raíz del repositorio y una instalación nueva del entorno virtual, siempre con el `PYTHONPATH` de ROS activo. En S1, los tests asíncronos necesitaron el plugin `anyio`, que ahora se activa de forma explícita: `addopts = ["--disable-plugin-autoload", "-p", "anyio"]`.

### Aprendizaje

- `pytest` funciona igual en cualquier máquina sin variables de entorno, y los plugins que usa el proyecto están declarados en su configuración.
- Queda un efecto menor documentado: `pip install` muestra avisos de dependencias de paquetes de ROS, porque también los ve a través de `PYTHONPATH`.

## 3. La redirección `/chat` → `/playground` era permanente

### Contexto

En S0.5 la pantalla de chat pasó a ser el Playground. La ruta antigua `/chat` se mantuvo para no romper enlaces y redirigía con `permanentRedirect()`, que responde con un 308.

### Síntomas

No hubo un fallo visible. El riesgo apareció al revisar el cierre de S0.5: los navegadores guardan en caché las redirecciones permanentes, y si en un sprint futuro `/chat` vuelve a ser una pantalla (por ejemplo, un chat con respuestas reales), quien ya hubiera visitado la ruta seguiría yendo a `/playground`.

### Diagnóstico

Era la única redirección del proyecto que no usaba `redirect()`. Ningún documento la describía como permanente.

### Solución

Cambié `permanentRedirect()` por `redirect()` en `frontend/src/app/chat/page.tsx`, que responde con un 307 temporal, y dejé en el código un comentario con el motivo.

La primera comprobación devolvió todavía `308 Permanent Redirect`. La causa no estaba en el cambio: un `next-server` y un `uvicorn` arrancados en una sesión anterior seguían en marcha, y la petición llegaba al servidor antiguo, con el build previo. Al parar el proceso envoltorio no se había parado el proceso hijo. Tras pararlos y repetir la prueba con el build nuevo:

```text
HTTP/1.1 307 Temporary Redirect
location: /playground
```

### Aprendizaje

- Las redirecciones de compatibilidad son temporales mientras la ruta pueda reutilizarse.
- Antes de interpretar un resultado compruebo qué proceso está escuchando en el puerto (`ss -ltnp`) y paro los servidores por grupo de procesos, no solo por el PID del envoltorio.
- Queda documentado que `/chat` es una página estática y la respuesta lleva `Cache-Control: s-maxage=31536000`: un CDN delante de la aplicación podría guardarla. Los navegadores ignoran `s-maxage`.

## 4. Validar PostgreSQL y Docker para S1 sin Docker en WSL

### Contexto

S1 introdujo PostgreSQL, migraciones con Alembic y un seed que se ejecuta al arrancar el contenedor del backend. Había que comprobar las migraciones contra un PostgreSQL real y el arranque completo con Docker Compose.

### Síntomas

En mi WSL no había ni Docker ni PostgreSQL, y no tenía permisos de administrador:

```text
The command 'docker' could not be found in this WSL 2 distro.
```

### Diagnóstico

- **PostgreSQL sin Docker.** Instalé `pgserver`, un paquete de Python que incluye los binarios de PostgreSQL 16.2, en un directorio temporal fuera del proyecto. El primer intento de conexión falló con `OSError: AF_UNIX path too long`: usaba como host la carpeta de datos, y el socket real estaba en `/run/user/1000/python_PostgresServer/…`, una ruta más corta.
- **Docker.** El comando `docker` de WSL no funcionaba porque la integración con WSL de Docker Desktop estaba desactivada, pero `docker.exe` de Windows sí respondía desde WSL (Docker Desktop 29.2.0 en marcha).

### Solución

Con PostgreSQL real, sobre bases de datos vacías:

- `alembic upgrade head` creó las dos tablas y sus nueve restricciones.
- `alembic check` confirmó que las migraciones coinciden con los modelos (`No new upgrade operations detected`).
- El ciclo `downgrade base` → `upgrade head` funcionó.
- El seed insertó 5 modelos y 5 precios; una segunda ejecución insertó 0.
- La suite completa pasó también contra PostgreSQL, incluido el test de migraciones.

Con `docker.exe` ejecuté el `docker-compose.yml` real como un proyecto aislado (`ai-router-s1-check`), con puertos distintos y un fichero de variables temporal, para no chocar con mi servidor de desarrollo ni usar mi `.env`:

- `docker compose up --build --wait`: PostgreSQL, backend y frontend llegaron a *healthy* en orden.
- Los logs del backend mostraron `Running upgrade  -> 0001` y `Seed completado: 5 modelos y 5 precios nuevos.`
- Tras reiniciar el backend: `Seed completado: 0 modelos y 0 precios nuevos.`
- `GET /api/v1/models` devolvió los 5 modelos y `POST /api/v1/route` la misma respuesta que antes de S1.
- El frontend del contenedor cargó la página Models y el Playground en un navegador.

Después eliminé el proyecto de prueba con sus contenedores, su volumen y sus imágenes.

### Aprendizaje

- El arranque con Docker (migraciones automáticas, seed idempotente y orden de servicios) está comprobado con un `docker compose up --build` real.
- La misma validación dejó a la vista limitaciones que siguen abiertas y están en el README: una `DATABASE_URL` con un formato distinto de `postgresql+asyncpg://…` impide arrancar el backend, y sin timeout de conexión un host de base de datos que no responde tarda unos 60 segundos en dar un 503.

## 5. Backend lanzado con `uvicorn app.main:app --reload`

### Contexto

Durante la auditoría de cierre de S1 encontré un proceso del backend lanzado con un comando que no es el del proyecto:

```text
uvicorn app.main:app --reload
```

### Síntomas

El proceso seguía vivo, pero no escuchaba en ningún puerto: la API no respondía a través de él.

### Diagnóstico

En este repositorio no existe un módulo `app.main`. El punto de entrada es `backend/main.py`, que expone `app`, así que la ruta de importación correcta es `main:app`. Con `--reload`, uvicorn deja vivo el proceso que vigila los cambios aunque la aplicación no llegue a cargarse, de modo que el proceso parece en marcha sin estar sirviendo nada.

Los problemas de puerto ocupado que vi en las mismas sesiones tenían otras causas, y los separo para no mezclarlas:

- Servidores de sesiones anteriores que seguían en marcha (incidente 3).
- Un backend que tardaba en liberar el puerto 8010 porque esperaba una petición colgada contra una base de datos que no respondía (incidente 6).

### Solución

Confirmé y dejé documentado el comando oficial:

- **En local:** `python main.py` desde `backend/`, que arranca uvicorn con autoreload en el entorno `development`.
- **En Docker:** `uvicorn main:app --host 0.0.0.0 --port 8010`, desde `scripts/docker-entrypoint.sh`, después de aplicar las migraciones.

Es el comando que usé para levantar el backend en la validación visual de S1.

### Aprendizaje

- El comando de arranque está en un solo sitio por entorno (README, `docs/DEVELOPMENT.md` y el entrypoint de Docker).
- Un proceso vivo no significa que la API esté sirviendo: compruebo el puerto y `GET /api/v1/health`.

## 6. Página Models sin backend o sin base de datos

### Contexto

La página Models de S1 carga el catálogo en el navegador desde `GET /api/v1/models`. Los tests y el build pasaban, pero la página no se había visto en un navegador real en todos sus estados.

### Síntomas

Sin backend o sin base de datos, la página muestra "No se pudo cargar el catálogo", y el detalle depende de la causa. Había que confirmar que cada caso mostraba el mensaje correcto y que el botón Reintentar recuperaba la página.

### Diagnóstico

Levanté el backend con `python main.py` contra bases de datos preparadas para cada caso y capturé la página con Chromium en modo headless (Playwright):

| Situación | Lo que muestra la página |
|---|---|
| Base de datos con el seed | Tabla con 5 modelos, Ollama Local como inactivo |
| Base de datos migrada pero vacía | "El catálogo está vacío" con el comando del seed |
| Host de base de datos que no responde | Filas de carga y "Cargando catálogo…"; a los 15 segundos, "El backend ha tardado demasiado en responder." |
| Base de datos caída (503) | "El catálogo de modelos no está disponible: no se pudo conectar con la base de datos." |
| Backend apagado | "No se pudo conectar con el backend (http://localhost:8010)." |
| Error y después Reintentar con la base de datos disponible | La tabla se carga |

La propia validación tuvo dos fallos que corregí antes de dar los resultados por buenos:

- La primera captura de éxito mostraba en realidad el estado de carga: el texto que esperaba el script ("activos para el enrutado") también aparece en la descripción de la página. Cambié la espera a un dato de la tabla ("Claude Sonnet").
- Algunos casos de error mostraban datos porque el backend anterior seguía en marcha: el PID que guardaba el script era el de un proceso intermedio que ya había terminado. Pasé a parar el backend por el grupo del proceso que escucha en el puerto 8010. Ese mismo backend, en el caso del host que no responde, tardaba en liberar el puerto porque esperaba la petición colgada.

### Solución

No hubo que cambiar código: la página ya gestionaba los estados de carga, vacío, error y reintento. En móvil no aparece scroll horizontal en la página, aunque las columnas de precio y estado quedan dentro del scroll de la tabla sin ninguna indicación visual.

### Aprendizaje

- Un estado de la interfaz solo lo doy por validado después de verlo en un navegador.
- Al automatizar capturas, espero a un dato que solo exista en el estado que quiero capturar.
- Siguen abiertos dos puntos: el mensaje del 503 dice "no se pudo conectar" también cuando la base de datos responde pero faltan las migraciones, y el aviso de scroll de la tabla en móvil.
