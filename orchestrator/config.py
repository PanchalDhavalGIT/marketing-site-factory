"""Configuration constants and environment variable handling."""

import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Directories
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
CLAUDE_DIR = PROJECT_ROOT / ".claude"
SKILLS_DIR = CLAUDE_DIR / "skills"
AGENTS_DIR = CLAUDE_DIR / "agents"

# Themes
THEMES_FILE = TEMPLATES_DIR / "themes.json"
INDUSTRY_DEFAULTS_FILE = TEMPLATES_DIR / "industry_defaults.json"

# Progress tracking
PROGRESS_FILE = LOGS_DIR / "progress.json"

# Concurrency
DEFAULT_CONCURRENCY = 5
MAX_CONCURRENCY = 10

# Session
DEFAULT_SESSION_TIMEOUT = 1800  # 30 minutes per site
MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 30  # seconds

# Claude CLI
CLAUDE_CMD = "claude"
CLAUDE_MAX_TURNS = 200
CLAUDE_OUTPUT_FORMAT = "json"

# Environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Required spreadsheet columns
REQUIRED_COLUMNS = [
    "business_name",
    "industry",
]

OPTIONAL_COLUMNS = [
    "description",
    "address",
    "phone",
    "email",
    "services",
    "website",
    "city",
    "state",
    "zip_code",
]


def validate_env() -> list[str]:
    """Check for missing environment variables. Returns list of warnings."""
    warnings = []
    if not GITHUB_TOKEN:
        warnings.append("GITHUB_TOKEN not set — deployment will fail (also run: gh auth login)")
    return warnings
