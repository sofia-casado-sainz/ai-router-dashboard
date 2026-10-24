# Guía de desarrollo

Documentación técnica para trabajar en el proyecto. Para una visión general, empieza por el [README](../README.md).

## Requisitos

- **Python ≥ 3.11**
- **Node.js ≥ 20** (recomendado 22) y npm
- **PostgreSQL ≥ 16** para ejecutar el backend en local (con Docker Compose ya viene incluido)
- **Docker** con Docker Compose v2 (opcional)

## Variables de entorno

```bash
cp .env.example .env                        # backend y docker compose
cp frontend/.env.example frontend/.env.local
```

| Variable | Uso | Por defecto |
|---|---|---|
| `API_URL` | URL del backend vista desde el navegador (sin `/api/v1`). En Docker se pasa al frontend como `NEXT_PUBLIC_API_URL`. | `http://localhost:8010` |
| `FRONTEND_URL` | Origen del frontend; el backend lo permite en CORS. | `http://localhost:3000` |
| `ENVIRONMENT` | `development` · `test` · `staging` · `production`. En `development`, `python main.py` usa autoreload. | `development` |
| `LOG_LEVEL` | `DEBUG` · `INFO` · `WARNING` · `ERROR` · `CRITICAL`. | `INFO` |
| `CORS_ORIGINS` | Orígenes CORS adicionales, separados por comas. | `http://127.0.0.1:3000` |
| `HOST` / `PORT` | Dirección del backend en local. | `127.0.0.1` / `8010` |
| `POSTGRES_*` | Conexión a PostgreSQL (`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`). Las usan el backend y Docker. `POSTGRES_PASSWORD` es obligatoria en Docker. | `localhost`, `5432`, `ai_router`, `ai_router` |
| `DATABASE_URL` | URL completa con driver asíncrono (`postgresql+asyncpg://…`). Si está definida, tiene prioridad sobre `POSTGRES_*`. | sin definir |
| `SEED_DATABASE` | Solo Docker: carga el catálogo de modelos de ejemplo al arrancar el backend. | `true` |

El backend lee, por orden de prioridad: variables de entorno, `backend/.env`, `.env` de la raíz y los valores por defecto de [`backend/core/config.py`](../backend/core/config.py). El frontend usa `frontend/.env.local` (`NEXT_PUBLIC_API_URL`).

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

alembic upgrade head         # crea o actualiza las tablas
python scripts/seed_models.py  # catálogo de modelos de ejemplo (idempotente)
python main.py               # http://localhost:8010  (Swagger en /docs)
pytest
```

### Base de datos

El backend usa PostgreSQL con SQLAlchemy 2 asíncrono (driver `asyncpg`) y Alembic para las migraciones. La app arranca aunque la base de datos no esté disponible: solo `GET /api/v1/models` responde `503`, y el router sigue funcionando porque todavía no la usa.

- **Migraciones:** viven en `backend/migrations/versions/` y solo contienen esquema, nunca datos. Para crear una nueva tras cambiar `database/models.py`, ejecuta `alembic revision --autogenerate -m "descripción"`, revisa el archivo generado y aplica con `alembic upgrade head`.
- **Seed:** `python scripts/seed_models.py` carga cinco modelos de ejemplo (GPT-5, Claude Sonnet, Gemini, DeepSeek y Ollama Local, este último inactivo). Los precios son datos de ejemplo, no tarifas reales. Solo inserta lo que falta, así que se puede repetir y no deshace cambios hechos a mano.
- **Fechas:** las columnas de fecha guardan zona horaria y las conexiones usan UTC.

### Tests del backend

La forma oficial de ejecutar los tests es `pytest` desde `backend/`, con el entorno virtual activado. También funcionan `python -m pytest` y `backend/.venv/bin/pytest backend` desde la raíz del repositorio. No hace falta ninguna variable de entorno.

Los tests que usan base de datos funcionan por defecto con SQLite (`aiosqlite`) en un archivo temporal, sin infraestructura. Para ejecutarlos contra PostgreSQL, define `TEST_DATABASE_URL` con una base de datos **exclusiva para tests**, porque se vacía en cada test:

```bash
TEST_DATABASE_URL=postgresql+asyncpg://usuario:clave@localhost:5432/ai_router_test pytest
```

Con PostgreSQL también se ejecuta `tests/test_migrations.py`: aplica y revierte las migraciones y comprueba que el esquema resultante coincide con los modelos ORM. Con SQLite ese test se omite.

La configuración vive en `[tool.pytest.ini_options]` de `pyproject.toml` e incluye `addopts = ["--disable-plugin-autoload"]`. Por defecto, pytest carga automáticamente cualquier plugin instalado que encuentre en `sys.path`, también los que no son del proyecto. En una máquina con ROS 2, `source /opt/ros/<distro>/setup.bash` exporta `PYTHONPATH` con los paquetes de ROS, y pytest intenta cargar sus plugins (`launch_testing`, `ament_*`). Fallan al importar dependencias que no están en el entorno virtual (por ejemplo, `ModuleNotFoundError: No module named 'lark'`) y los tests no llegan a ejecutarse. Con la carga automática desactivada, el resultado no depende de lo que haya instalado en el sistema.

El flag existe desde pytest 8.4, por eso es la versión mínima en las dependencias de desarrollo. Los plugins que necesita el proyecto se activan explícitamente en `addopts`: hoy solo `-p anyio`, que ejecuta los tests asíncronos marcados con `@pytest.mark.anyio`.

Los logs salen en JSON, una línea por evento:

```json
{"timestamp": "2026-10-22T11:39:51.854+00:00", "level": "INFO", "module": "main", "logger": "main", "message": "Aplicación iniciada", "environment": "development", "version": "0.1.0"}
```

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/health` | Estado del servicio → `{"status": "ok"}` |
| `POST` | `/api/v1/route` | Recibe `{"prompt": "..."}` y devuelve el modelo seleccionado, la complejidad, el coste estimado y el motivo. |
| `GET` | `/api/v1/models` | Catálogo de modelos con su precio vigente. `?active_only=true` devuelve solo los activos. `503` si la base de datos no está disponible. |

## Frontend

```bash
cd frontend
npm install
npm run dev                  # http://localhost:3000
npm run lint
npm run typecheck
npm run build
```

## Validación del frontend

Tres comprobaciones independientes entre sí: funcionan en cualquier orden y en un clon limpio, tras `npm ci`, sin artefactos de ejecuciones anteriores.

| Comando | Qué comprueba | Notas |
|---|---|---|
| `npm run lint` | ESLint con `eslint-config-next`: reglas de React, hooks, accesibilidad y Next.js. | No necesita tipos generados. |
| `npm run typecheck` | TypeScript estricto en todo el proyecto, incluidos los tipos que Next.js genera para rutas y layouts. | `next typegen && tsc --noEmit`. No compila la aplicación; tarda unos segundos. |
| `npm run build` | Build de producción: compila, comprueba tipos y prerenderiza las rutas. | `next build` no ejecuta ESLint en esta versión de Next.js, por eso `lint` va aparte. |

### Por qué `typecheck` usa `next typegen`

Next.js genera tipos a partir de la estructura de `src/app`: helpers globales como `LayoutProps` (los usa `src/app/layout.tsx`), la lista de rutas de la aplicación y un validador que comprueba que cada página y cada layout exportan lo que Next.js espera. Esos tipos se escriben en `.next/types/` y `next-env.d.ts`, que no están en git.

`next build` y `next dev` los generan, pero `tsc` por sí solo no. Por eso, en un clon limpio, `tsc --noEmit` falla con `Cannot find name 'LayoutProps'`. `next typegen` genera esos archivos sin hacer un build completo, así que `typecheck` funciona desde cero y siempre con los tipos al día: si borras o renombras una ruta, los vuelve a generar.

## Docker Compose

```bash
cp .env.example .env         # define POSTGRES_PASSWORD
docker compose up --build
```

| Servicio | URL |
|---|---|
| frontend | <http://localhost:3000> |
| backend | <http://localhost:8010/docs> |
| postgres | `localhost:5432` (volumen `postgres-data`) |

- `API_URL` se incrusta en el bundle del frontend **al construir la imagen**. Si lo cambias, ejecuta `docker compose build frontend`.
- El backend espera a que PostgreSQL esté sano, aplica las migraciones y, con `SEED_DATABASE=true` (por defecto), carga el catálogo de ejemplo antes de arrancar.

## Contrato frontend ↔ backend

Tras cambiar un endpoint o schema:

```bash
cd backend && python scripts/export_openapi.py   # regenera contracts/openapi.json
```

Después actualiza [`frontend/src/types/api.ts`](../frontend/src/types/api.ts). El test `tests/test_contract.py` falla si el contrato está desactualizado. Más detalles en [contracts/README.md](../contracts/README.md).

## Estructura de carpetas

```
ai-router-dashboard/
├── backend/
│   ├── main.py                  # create_app(): CORS, logging, motor de BD, routers en /api/v1
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── api/                     # routes.py (endpoints) · dependencies.py (sesión y servicios)
│   ├── core/                    # config.py (Settings) · logging.py (JSON)
│   ├── domain/                  # objetos de dominio sin dependencias (CatalogModel, ModelPrice)
│   ├── database/                # base, modelos ORM, sesiones y seed
│   ├── migrations/              # Alembic (env.py asíncrono + versions/)
│   ├── repositories/            # acceso a datos; devuelven objetos de dominio
│   ├── router/                  # catalog.py (catálogo interno del router) · model_selector.py (reglas)
│   ├── schemas/                 # modelos Pydantic de entrada/salida
│   ├── services/                # routing_service · model_catalog_service
│   ├── scripts/                 # export_openapi.py · seed_models.py · docker-entrypoint.sh
│   └── tests/                   # conftest.py: SQLite por defecto, PostgreSQL con TEST_DATABASE_URL
├── frontend/src/
│   ├── app/                     # rutas: playground (inicio), dashboard, analytics, models, settings; /chat redirige a /playground (temporal, 307)
│   ├── components/              # playground/, dashboard/, models/, layout/
│   ├── hooks/                   # usePlaygroundRouter, useModelCatalog, useBackendHealth, useDisclosure
│   ├── lib/                     # config, formato, estilos de modelos
│   ├── services/                # apiClient (HTTP), routerApi y modelsApi (backend real), api + mockData (dashboard)
│   └── types/                   # api.ts (contrato HTTP), playground.ts, models.ts, index.ts
├── contracts/openapi.json
├── docs/
├── docker-compose.yml
└── .env.example
```

## Solución de problemas

- **`pytest` falla al cargar plugins ajenos al proyecto** (por ejemplo, con ROS 2 y su `PYTHONPATH` exportado): ya no debería ocurrir, porque la configuración desactiva la carga automática de plugins (ver [Tests del backend](#tests-del-backend)). Si vuelve a pasar, comprueba que tienes pytest ≥ 8.4 en el entorno virtual (`pip install -e ".[dev]"`).
- **`pip install` avisa de dependencias de paquetes de ROS** (por ejemplo, `launch-ros requires setuptools`): pip también ve los paquetes de ROS a través de `PYTHONPATH`. Es inofensivo; para una instalación sin ruido, ejecútalo en una terminal sin ROS cargado o con `PYTHONPATH= pip install -e ".[dev]"`.
- **`GET /api/v1/models` responde 503 o la página Models muestra "No se pudo cargar el catálogo"**: el backend no llega a PostgreSQL. Comprueba que está levantado, las variables `POSTGRES_*` o `DATABASE_URL` y que has ejecutado `alembic upgrade head`.
- **La página Models muestra "El catálogo está vacío"**: las tablas existen pero no hay datos; ejecuta `python scripts/seed_models.py`.
- **El Playground muestra "No se pudo conectar con el backend"**: comprueba que el backend está levantado y que `NEXT_PUBLIC_API_URL` apunta a él, sin `/api/v1`.
- **`typecheck` o `build` fallan con errores en `.next/dev/types/validator.ts` después de borrar o renombrar una ruta**: son tipos obsoletos de una sesión anterior de `npm run dev`. Next.js los guarda en `.next/dev`, y ni `next typegen` ni `next build` los regeneran. Borra la carpeta con `rm -rf frontend/.next/dev`; se vuelve a crear al arrancar `npm run dev`. En CI no ocurre, porque el clon empieza limpio.
