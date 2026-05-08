from __future__ import annotations

# main.py — creates the FastAPI server and wires up routes + background refresh
# This is the backend entrypoint used by Uvicorn (the local dev web server).

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.settings import get_settings
from backend.app.services.refresh_scheduler import start_scheduler
from backend.app.routes.tables import router as tables_router
from backend.app.routes.admin_refresh import router as admin_router


def create_app() -> FastAPI:
    # Build and configure the FastAPI application instance.
    # Returns: a ready-to-run FastAPI app object.
    app = FastAPI(title="Savings Yield Optimiser API")

    # Allow the local frontend (Vite dev server) to call the API in development.
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
    app.include_router(admin_router)

    # Set a default log level so refresh jobs and API logs show up clearly.
    logging.basicConfig(level=logging.INFO)
    scheduler_holder: dict[str, object] = {}

    @app.on_event("startup")
    def _startup() -> None:
        # When the API starts, optionally start the 6-hour refresh scheduler (if enabled via env vars).
        settings = get_settings()
        scheduler_holder["scheduler"] = start_scheduler(settings=settings)

    @app.on_event("shutdown")
    def _shutdown() -> None:
        # When the API stops, try to shut down the scheduler cleanly to avoid leaving threads running.
        sched = scheduler_holder.get("scheduler")
        if sched is not None:
            try:
                sched.shutdown(wait=False)  # type: ignore[attr-defined]
            except Exception:
                logging.getLogger(__name__).exception("Failed to shut down scheduler cleanly.")

    @app.get("/health")
    def health() -> dict[str, str]:
        # Simple endpoint to confirm the backend is running and where the SQLite DB is located.
        # Returns: status + db_path as strings.
        settings = get_settings()
        return {
            "status": "ok",
            "db_path": str(settings.db_path),
        }

    return app


# Export a module-level `app` so `uvicorn backend.app.main:app` works.
app = create_app()

