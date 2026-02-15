"""HTML page routes — serves full pages via Jinja2 templates."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from dashboard.state import state

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Dashboard overview page."""
    stats = state.get_stats()
    return request.app.state.templates.TemplateResponse(
        "index.html", {"request": request, "stats": stats}
    )


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Spreadsheet upload page."""
    return request.app.state.templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "businesses": state.businesses,
            "spreadsheet_name": state.spreadsheet_name,
        },
    )


@router.get("/monitor", response_class=HTMLResponse)
async def monitor_page(request: Request):
    """Real-time build monitoring page."""
    progress = state.get_progress()
    stats = state.get_stats()
    return request.app.state.templates.TemplateResponse(
        "monitor.html",
        {"request": request, "progress": progress, "stats": stats},
    )


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Log viewer page."""
    log_files = state.get_log_files()
    return request.app.state.templates.TemplateResponse(
        "logs.html", {"request": request, "log_files": log_files}
    )


@router.get("/logs/{slug}", response_class=HTMLResponse)
async def log_detail(request: Request, slug: str):
    """Individual site log viewer."""
    lines = state.read_log(slug, tail=200)
    return request.app.state.templates.TemplateResponse(
        "log_detail.html",
        {"request": request, "slug": slug, "lines": lines},
    )


@router.get("/sites", response_class=HTMLResponse)
async def sites_page(request: Request):
    """Deployed sites listing."""
    deployed = state.get_deployed_sites()
    return request.app.state.templates.TemplateResponse(
        "sites.html", {"request": request, "deployed": deployed}
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings and configuration page."""
    return request.app.state.templates.TemplateResponse(
        "settings.html", {"request": request, "settings": state.settings}
    )
