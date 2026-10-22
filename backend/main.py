import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="AI Router API",
    description="Backend del AI Router Dashboard: selección automática de modelos de IA.",
    version="0.1.0",
)

# Orígenes del frontend permitidos (separados por comas).
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    # Puerto configurable; 8010 por defecto para no chocar con el 8000.
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8010")),
        reload=True,
    )
