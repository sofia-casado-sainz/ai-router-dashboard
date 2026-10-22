# AI Router Dashboard

Router inteligente de IA: analiza cada prompt y elige automáticamente el modelo más adecuado (GPT, Claude, Gemini, DeepSeek y, más adelante, modelos locales con Ollama) según coste, calidad y complejidad. Incluye un dashboard para controlar consumo, coste y ahorro.

> **Estado actual (Sprint S0, Fundaciones).** El enrutado está **simulado** con reglas de palabras clave y precios ficticios. Todavía no se llama a ningún proveedor de IA, no hay base de datos conectada ni autenticación. Las métricas del dashboard son datos de ejemplo.

## Arquitectura actual

```
Navegador ──► Frontend (Next.js 16, :3000)
                 │  fetch  {API_URL}/api/v1/...
                 ▼
              Backend (FastAPI, :8010)
                 api/routes ──► services ──► router (reglas + catálogo de modelos)

              PostgreSQL 17 (:5432): solo infraestructura, aún sin conectar
```

| Pieza | Descripción |
|---|---|
| **Frontend** | Next.js (App Router), React 19, Tailwind 4. Páginas: Dashboard, Chat Router, Analytics, Models y Settings (estas tres últimas, "Próximamente"). |
| **Backend** | FastAPI con configuración centralizada (`pydantic-settings`), logging JSON y API versionada en `/api/v1`. |
| **Catálogo de modelos** | Única fuente de verdad en `backend/router/catalog.py`. El frontend recibe id, nombre y proveedor en cada respuesta y aplica un estilo neutro a modelos que no conoce. |
| **Contrato** | `contracts/openapi.json`, exportado desde FastAPI (ver [contracts/README.md](contracts/README.md)). |

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/health` | Estado del servicio → `{"status": "ok"}` |
| `POST` | `/api/v1/route` | Recibe `{"prompt": "..."}` y devuelve el modelo seleccionado, la complejidad, el coste estimado y el motivo. |

Documentación interactiva: <http://localhost:8010/docs>.

## Requisitos

- **Python ≥ 3.11**
- **Node.js ≥ 20** (recomendado 22) y npm
- **Docker** con Docker Compose v2 (opcional, para levantarlo todo junto)

## Arranque local

### 1. Variables de entorno

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
| `POSTGRES_*` | Credenciales de PostgreSQL en Docker. `POSTGRES_PASSWORD` es obligatoria. | ver `.env.example` |

El backend lee, por orden de prioridad: variables de entorno, `backend/.env`, `.env` de la raíz y los valores por defecto de [`backend/core/config.py`](backend/core/config.py). El frontend usa `frontend/.env.local` (`NEXT_PUBLIC_API_URL`).

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

python main.py               # http://localhost:8010  (docs en /docs)
pytest                       # tests
```

Los logs salen en JSON, una línea por evento:

```json
{"timestamp": "2026-10-22T11:39:51.854+00:00", "level": "INFO", "module": "main", "logger": "main", "message": "Aplicación iniciada", "environment": "development", "version": "0.1.0"}
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                  # http://localhost:3000
npm run lint
npm run build
```

## Docker Compose

Levanta el frontend, el backend y PostgreSQL:

```bash
cp .env.example .env         # y define POSTGRES_PASSWORD
docker compose up --build
```

| Servicio | URL |
|---|---|
| frontend | <http://localhost:3000> |
| backend | <http://localhost:8010/docs> |
| postgres | `localhost:5432` (volumen `postgres-data`) |

- `API_URL` se incrusta en el bundle del frontend **al construir la imagen**. Si lo cambias, ejecuta `docker compose build frontend`.
- PostgreSQL arranca con healthcheck y volumen persistente, pero el backend aún no se conecta a él (Sprint S1).

## Contrato frontend ↔ backend

Tras cambiar un endpoint o schema:

```bash
cd backend && python scripts/export_openapi.py   # regenera contracts/openapi.json
```

Después actualiza [`frontend/src/types/api.ts`](frontend/src/types/api.ts). El test `tests/test_contract.py` falla si el contrato está desactualizado. En el Sprint S1 los tipos TypeScript se generarán automáticamente desde `openapi.json`.

## Estructura de carpetas

```
ai-router-dashboard/
├── backend/
│   ├── main.py                  # create_app(): CORS, logging, routers en /api/v1
│   ├── pyproject.toml           # dependencias y configuración de pytest
│   ├── Dockerfile
│   ├── api/routes.py            # endpoints HTTP
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   └── logging.py           # formatter JSON
│   ├── router/
│   │   ├── catalog.py           # catálogo de modelos (fuente de verdad)
│   │   └── model_selector.py    # reglas de enrutado y estimación de coste
│   ├── schemas/                 # modelos Pydantic de entrada/salida
│   ├── services/                # orquestación entre API y dominio
│   ├── scripts/export_openapi.py
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── next.config.ts           # output "standalone" para Docker
│   └── src/
│       ├── app/                 # rutas: dashboard, chat, analytics, models, settings
│       ├── components/          # chat/, dashboard/, layout/
│       ├── hooks/               # useChatRouter, useBackendHealth, useDisclosure
│       ├── lib/                 # config, formato, estilos de modelos
│       ├── services/            # routerApi (backend real), api + mockData (dashboard)
│       └── types/               # api.ts (contrato HTTP), chat.ts, index.ts
├── contracts/openapi.json       # contrato OpenAPI exportado del backend
├── docker-compose.yml
└── .env.example
```

## Solución de problemas

- **`pytest` falla al cargar plugins ajenos al proyecto** (por ejemplo, con ROS instalado y su `PYTHONPATH` exportado): ejecuta `PYTHONPATH= pytest`.
- **El chat muestra "No se pudo conectar con el backend"**: comprueba que el backend está levantado y que `NEXT_PUBLIC_API_URL` apunta a él, sin `/api/v1`.
