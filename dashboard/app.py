"""
Marketing Site Factory — Dashboard Application.

Run with:
    python -m dashboard.app

Or:
    uvicorn dashboard.app:app --reload --port 3000
"""

import uvicorn
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from dashboard.routes.pages import router as pages_router
from dashboard.routes.api import router as api_router

TEMPLATE_DIR = Path(__file__).parent / "templates"

app = FastAPI(
    title="Marketing Site Factory",
    description="Control dashboard for batch marketing site generation",
)

# Templates
app.state.templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Routes
app.include_router(pages_router)
app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(
        "dashboard.app:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
    )
