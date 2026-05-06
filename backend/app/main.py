from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.settings import get_settings
from backend.app.routes.tables import router as tables_router


def create_app() -> FastAPI:
    app = FastAPI(title="Savings Yield Optimiser API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(tables_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        settings = get_settings()
        return {
            "status": "ok",
            "db_path": str(settings.db_path),
        }

    return app


app = create_app()

