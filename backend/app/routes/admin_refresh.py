from __future__ import annotations

# admin_refresh.py — admin-only endpoints to manually run a refresh and see job status
# These endpoints are protected by a shared secret header (X-Admin-Token).

import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from backend.app.services.refresh_scheduler import run_refresh_once
from backend.app.db.connection import connection
from backend.app.settings import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


Status = Literal["queued", "running", "succeeded", "failed"]


def _now_iso_z() -> str:
    # Build a “UTC ISO timestamp” string like 2026-01-01T12:34:56.789Z.
    # Returns: a string timestamp used for job start/finish times.
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass
class JobState:
    job_id: str
    status: Status
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None


_jobs: dict[str, JobState] = {}
_lock = threading.Lock()


def _require_admin(
    x_admin_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    # Enforce that the request includes the correct admin token.
    # Inputs: X-Admin-Token header (string) and Settings (where ADMIN_TOKEN lives).
    # Returns: nothing (raises an HTTP error if unauthorized).
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail="Admin token not configured on server.")
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/refresh")
def trigger_refresh(
    wait: bool = Query(
        False,
        description="If true, run refresh synchronously and return success only when complete.",
    ),
    _: None = Depends(_require_admin),
) -> dict[str, str]:
    # Start a refresh run (scrape + upsert) either synchronously (wait=true) or in a background thread.
    # Inputs:
    # - wait: if true, this request blocks until refresh completes
    # Returns: a small JSON object with job_id and status/message for the UI.
    job_id = uuid.uuid4().hex
    state = JobState(job_id=job_id, status="queued")
    with _lock:
        _jobs[job_id] = state

    # Persist job run record (survives restarts)
    settings = get_settings()
    with connection(settings.db_path) as conn:
        # We write "running" immediately so the job shows up in history right away.
        conn.execute(
            """
            INSERT INTO ingestion_job_run(job_run_id, job_type, status, started_at)
            VALUES (?, ?, ?, ?);
            """,
            (job_id, "admin", "running", _now_iso_z()),
        )

    if wait:
        with _lock:
            _jobs[job_id].status = "running"
            _jobs[job_id].started_at = _now_iso_z()
        try:
            run_refresh_once(settings=settings)
            with _lock:
                _jobs[job_id].status = "succeeded"
                _jobs[job_id].finished_at = _now_iso_z()
            with connection(settings.db_path) as conn:
                # Mark the persisted job record as succeeded so we can view it after restarts.
                conn.execute(
                    """
                    UPDATE ingestion_job_run
                    SET status=?, finished_at=?
                    WHERE job_run_id=?;
                    """,
                    ("succeeded", _now_iso_z(), job_id),
                )
            return {"job_id": job_id, "status": "succeeded", "message": "Refresh complete"}
        except Exception as e:
            logger.exception("Synchronous refresh failed job_id=%s", job_id)
            with _lock:
                _jobs[job_id].status = "failed"
                _jobs[job_id].finished_at = _now_iso_z()
                _jobs[job_id].error = str(e)
            with connection(settings.db_path) as conn:
                # Store the error message (best-effort) so we can debug failures later.
                conn.execute(
                    """
                    UPDATE ingestion_job_run
                    SET status=?, finished_at=?, error=?
                    WHERE job_run_id=?;
                    """,
                    ("failed", _now_iso_z(), str(e), job_id),
                )
            raise HTTPException(status_code=500, detail="Refresh failed") from e

    def _runner() -> None:
        # Background worker that runs the refresh and then updates job status.
        with _lock:
            _jobs[job_id].status = "running"
            _jobs[job_id].started_at = _now_iso_z()
        try:
            settings = get_settings()
            run_refresh_once(settings=settings)
            with _lock:
                _jobs[job_id].status = "succeeded"
                _jobs[job_id].finished_at = _now_iso_z()
            with connection(settings.db_path) as conn:
                # Persist success to SQLite so history survives process restarts.
                conn.execute(
                    """
                    UPDATE ingestion_job_run
                    SET status=?, finished_at=?
                    WHERE job_run_id=?;
                    """,
                    ("succeeded", _now_iso_z(), job_id),
                )
        except Exception as e:
            logger.exception("Manual refresh job failed job_id=%s", job_id)
            with _lock:
                _jobs[job_id].status = "failed"
                _jobs[job_id].finished_at = _now_iso_z()
                _jobs[job_id].error = str(e)
            with connection(settings.db_path) as conn:
                # Persist failure details so we can inspect history later.
                conn.execute(
                    """
                    UPDATE ingestion_job_run
                    SET status=?, finished_at=?, error=?
                    WHERE job_run_id=?;
                    """,
                    ("failed", _now_iso_z(), str(e), job_id),
                )

    t = threading.Thread(target=_runner, name=f"manual-refresh-{job_id}", daemon=True)
    t.start()

    return {"job_id": job_id, "status": "queued", "message": "Refresh started"}


@router.get("/refresh/{job_id}")
def get_refresh_status(job_id: str, _: None = Depends(_require_admin)) -> dict[str, str | None]:
    # Return the in-memory status for a job started in this running server process.
    # Note: this does NOT survive server restarts (use /refresh-history for persisted status).
    with _lock:
        state = _jobs.get(job_id)
        if not state:
            raise HTTPException(status_code=404, detail="Job not found")
        return {
            "job_id": state.job_id,
            "status": state.status,
            "started_at": state.started_at,
            "finished_at": state.finished_at,
            "error": state.error,
        }


@router.get("/refresh-history")
def get_refresh_history(
    limit: int = Query(25, ge=1, le=200),
    settings: Settings = Depends(get_settings),
    _: None = Depends(_require_admin),
) -> dict[str, list[dict[str, str | None]]]:
    # Return a list of recent refresh runs from SQLite (survives restarts).
    # Inputs: limit (how many rows to return).
    # Returns: {"items": [...]} with timestamps and optional error messages.
    with connection(settings.db_path) as conn:
        rows = conn.execute(
            """
            SELECT job_run_id, job_type, status, started_at, finished_at, error
            FROM ingestion_job_run
            ORDER BY started_at DESC
            LIMIT ?;
            """,
            (limit,),
        ).fetchall()

    items: list[dict[str, str | None]] = []
    for r in rows:
        items.append(
            {
                "job_run_id": str(r["job_run_id"]),
                "job_type": str(r["job_type"]),
                "status": str(r["status"]),
                "started_at": str(r["started_at"]),
                "finished_at": str(r["finished_at"]) if r["finished_at"] is not None else None,
                "error": str(r["error"]) if r["error"] is not None else None,
            }
        )
    return {"items": items}

