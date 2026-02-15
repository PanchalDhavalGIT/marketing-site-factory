"""API routes — HTMX endpoints for dynamic updates and actions."""

import shutil
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse

from orchestrator.config import DATA_DIR, MAX_CONCURRENCY
from dashboard.state import state

router = APIRouter(prefix="/api")


# ── Upload ───────────────────────────────────────────────────────

@router.post("/upload", response_class=HTMLResponse)
async def upload_spreadsheet(
    request: Request,
    file: UploadFile = File(...),
    count: int = Form(default=0),
):
    """Upload and parse a spreadsheet file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dest = DATA_DIR / file.filename
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        loaded = state.load_spreadsheet(dest, count=count if count > 0 else None)
        return request.app.state.templates.TemplateResponse(
            "partials/upload_result.html",
            {
                "request": request,
                "success": True,
                "message": f"Loaded {loaded} businesses from {file.filename}",
                "businesses": state.businesses,
            },
        )
    except Exception as e:
        return request.app.state.templates.TemplateResponse(
            "partials/upload_result.html",
            {"request": request, "success": False, "message": str(e), "businesses": []},
        )


# ── Batch Control ────────────────────────────────────────────────

@router.post("/batch/start", response_class=HTMLResponse)
async def start_batch(
    request: Request,
    count: int = Form(default=0),
    concurrency: int = Form(default=5),
):
    """Start a batch build job."""
    msg = await state.start_batch(
        count=count if count > 0 else None,
        concurrency=min(concurrency, MAX_CONCURRENCY),
    )
    stats = state.get_stats()
    return request.app.state.templates.TemplateResponse(
        "partials/batch_status.html",
        {"request": request, "message": msg, "stats": stats},
    )


@router.post("/batch/stop", response_class=HTMLResponse)
async def stop_batch(request: Request):
    """Stop the running batch."""
    msg = await state.stop_batch()
    stats = state.get_stats()
    return request.app.state.templates.TemplateResponse(
        "partials/batch_status.html",
        {"request": request, "message": msg, "stats": stats},
    )


# ── Progress (HTMX polling) ─────────────────────────────────────

@router.get("/progress", response_class=HTMLResponse)
async def get_progress(request: Request):
    """Return progress table partial (polled by HTMX every 3s)."""
    progress = state.get_progress()
    stats = state.get_stats()
    return request.app.state.templates.TemplateResponse(
        "partials/progress_table.html",
        {"request": request, "progress": progress, "stats": stats},
    )


@router.get("/stats", response_class=HTMLResponse)
async def get_stats(request: Request):
    """Return stats cards partial (polled by HTMX)."""
    stats = state.get_stats()
    return request.app.state.templates.TemplateResponse(
        "partials/stats_cards.html",
        {"request": request, "stats": stats},
    )


# ── Logs ─────────────────────────────────────────────────────────

@router.get("/logs/{slug}/content", response_class=HTMLResponse)
async def get_log_content(request: Request, slug: str):
    """Return log content partial (polled by HTMX)."""
    lines = state.read_log(slug, tail=100)
    return request.app.state.templates.TemplateResponse(
        "partials/log_content.html",
        {"request": request, "slug": slug, "lines": lines},
    )


# ── Retry ────────────────────────────────────────────────────────

@router.post("/retry/{slug}", response_class=HTMLResponse)
async def retry_site(request: Request, slug: str):
    """Retry building a specific failed site."""
    msg = await state.retry_site(slug)
    progress = state.get_progress()
    stats = state.get_stats()
    return request.app.state.templates.TemplateResponse(
        "partials/progress_table.html",
        {"request": request, "progress": progress, "stats": stats, "message": msg},
    )


# ── Cleanup ──────────────────────────────────────────────────────

@router.post("/clear/progress", response_class=HTMLResponse)
async def clear_progress(request: Request):
    """Clear all progress data."""
    msg = state.clear_progress()
    return HTMLResponse(f'<div class="text-green-400 text-sm">{msg}</div>')


@router.post("/clear/workspaces", response_class=HTMLResponse)
async def clear_workspaces(request: Request):
    """Clear all workspace directories."""
    msg = state.clear_workspaces()
    return HTMLResponse(f'<div class="text-green-400 text-sm">{msg}</div>')


# ── Settings ─────────────────────────────────────────────────────

@router.post("/settings", response_class=HTMLResponse)
async def update_settings(
    request: Request,
    concurrency: int = Form(default=5),
    timeout: int = Form(default=1800),
):
    """Update runtime settings."""
    import orchestrator.config as config

    state.concurrency = min(concurrency, MAX_CONCURRENCY)
    state.settings["concurrency"] = state.concurrency
    state.settings["session_timeout"] = timeout
    config.DEFAULT_SESSION_TIMEOUT = timeout

    return HTMLResponse(
        '<div class="text-green-400 text-sm mt-2">Settings saved.</div>'
    )


# ── JSON API (for external integrations) ─────────────────────────

@router.get("/v1/status", response_class=JSONResponse)
async def api_status():
    """JSON status endpoint for external tools."""
    return {
        "stats": state.get_stats(),
        "progress": state.get_progress(),
        "deployed": state.get_deployed_sites(),
    }
