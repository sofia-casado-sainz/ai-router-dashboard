# Publicación

Preparación para publicar el proyecto en GitHub: metadatos del repositorio, textos de release, checklist de la demo pública y la CI prevista. Nada de esto está aplicado todavía; se configura a mano cuando toque.

## Metadatos del repositorio

Se configuran en GitHub, en **About** (rueda dentada de la página principal del repositorio).

**Descripción**

- Inglés: `Picks which AI model should handle each task and explains why. Next.js + FastAPI + PostgreSQL. Work in progress.`
- Español: `Elige qué modelo de IA usar para cada tarea y explica por qué. Next.js + FastAPI + PostgreSQL. Prototipo en desarrollo.`

El README principal está en inglés, así que la descripción en inglés es la recomendada.

**Topics**

`llm` `ai` `model-routing` `llm-router` `fastapi` `nextjs` `typescript` `python` `postgresql` `sqlalchemy` `alembic` `docker` `openapi`

**Website:** vacío hasta que exista la demo pública.

## Versiones

Las etiquetas de git siguen los sprints cerrados:

| Etiqueta | Contenido |
|---|---|
| `v0.5.0` | Cierre de S0.5: Playground, navegación honesta y endurecimiento |
| `v0.6.0` | Cierre de S1: catálogo persistente de modelos |
| `v0.6.1` | Cierre de S1.5: documentación, licencia y preparación de publicación (solo documentación) |

Las versiones de `frontend/package.json`, `backend/pyproject.toml` y `app_version` siguen en `0.1.0`. Alinearlas cambia `info.version` en `contracts/openapi.json`, así que se hará en un sprint que pueda tocar la API.

## Texto de release: v0.6.0

```markdown
## v0.6.0 · Catálogo persistente de modelos (Sprint S1)

### Novedades
- Catálogo de modelos en PostgreSQL (SQLAlchemy 2 asíncrono + asyncpg) con histórico de precios.
- Migraciones con Alembic (`0001_create_model_catalog`) y seed idempotente con 5 modelos de ejemplo.
- `GET /api/v1/models`: modelos con proveedor, ventana de contexto, estado y precio vigente (`?active_only=true` para ver solo los activos).
- Página Models conectada a la API, con estados de carga, vacío, error y reintento.
- Docker Compose: el backend espera a PostgreSQL, aplica las migraciones y carga el seed al arrancar.

### Compatibilidad
- El router no cambia: `POST /api/v1/route` devuelve exactamente lo mismo que en v0.5.0, y un test lo comprueba.

### Cómo actualizar
- Hace falta PostgreSQL. En local: `alembic upgrade head` y `python scripts/seed_models.py`. Con Docker es automático.

### Limitaciones conocidas
- Los precios del catálogo son de ejemplo, no tarifas reales.
- El router todavía usa su catálogo interno; se conectará al persistente en S2.
- `DATABASE_URL` debe usar `postgresql+asyncpg://`.
```

## Texto de release: v0.6.1

```markdown
## v0.6.1 · Portfolio y open source (Sprint S1.5)

Versión solo de documentación: no cambia el código, la API ni la base de datos.

- README en inglés (`README.md`) y en español (`README.es.md`), con la historia del proyecto, el uso de IA, las limitaciones conocidas y la diferencia frente a OpenRouter Auto y al uso directo de asistentes.
- Lecciones aprendidas corregidas y roadmap actualizado.
- Caso de estudio reescrito en `docs/PORTFOLIO.md`.
- Licencia MIT.
- `docs/PUBLISHING.md`: metadatos, releases, checklist de demo y CI prevista.
```

## Checklist de la demo pública

- [ ] **URL de la base de datos.** Los proveedores (Neon, Render, Supabase…) suelen dar `postgresql://…`. Hay que cambiarla a `postgresql+asyncpg://…`; con otro formato el backend no arranca.
- [ ] `NEXT_PUBLIC_API_URL` definida al **construir** el frontend, apuntando a la URL pública del backend.
- [ ] `FRONTEND_URL` (y `CORS_ORIGINS` si hace falta) en el backend con la URL pública del frontend.
- [ ] Migraciones y seed aplicados en la base de datos de la demo.
- [ ] La interfaz deja claro que los precios son de ejemplo y que el dashboard usa datos de ejemplo.
- [ ] Ningún secreto en el repositorio (`.env` está en `.gitignore`).
- [ ] `/api/v1/route` y `/api/v1/models` no tienen autenticación ni límite de peticiones. Hoy no llaman a ningún modelo, pero hay que revisarlo antes de S2.
- [ ] Arranque en frío de los planes gratuitos: avisarlo en la página o asumirlo.
- [ ] Probar en la demo: el Playground con un ejemplo, la página Models y la documentación de la API en `/docs`.
- [ ] Añadir la URL al README, al campo **Website** del repositorio y a LinkedIn.

## CI prevista

### Propuesta

- **Cuándo:** en cada push a `main` y en cada pull request.
- **Frontend:** `npm ci`, `npm run lint`, `npm run typecheck` y `npm run build`, con Node 22. Se usa `npm run typecheck` y no `tsc` a secas, porque en un clon limpio hacen falta los tipos que genera `next typegen`.
- **Backend:** `pytest` con Python 3.11 (versión mínima) y 3.12 (la de la imagen Docker), contra un PostgreSQL real, para que `tests/test_migrations.py` no se omita.
- **Seguridad:** permisos de solo lectura, cancelación de ejecuciones anteriores de la misma rama y timeout por job.
- **Al implementarla:** fijar las actions por SHA en lugar de por etiqueta y añadir el badge al README.

### Workflow recomendado

Ruta: `.github/workflows/ci.yml`.

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  frontend:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm run build

  backend:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      matrix:
        python: ["3.11", "3.12"]
    services:
      postgres:
        image: postgres:17-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: ai_router_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U test -d ai_router_test"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10
    env:
      TEST_DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/ai_router_test
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
          cache: pip
          cache-dependency-path: backend/pyproject.toml
      - run: pip install -e ".[dev]"
      - run: pytest
```

### Badge recomendado

Se añade al README, junto al resto de badges, cuando el workflow exista:

```markdown
![CI](https://github.com/sofia-casado-sainz/ai-router-dashboard/actions/workflows/ci.yml/badge.svg)
```
