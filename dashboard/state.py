"""
Shared dashboard state — bridges the dashboard UI with the orchestrator engine.
Manages loaded spreadsheet data, active batch jobs, and configuration.
"""

import asyncio
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from orchestrator.config import (
    DATA_DIR,
    LOGS_DIR,
    PROGRESS_FILE,
    WORKSPACE_DIR,
    PROJECT_ROOT,
    DEFAULT_CONCURRENCY,
    MAX_CONCURRENCY,
)
from orchestrator.spreadsheet_reader import read_spreadsheet
from orchestrator.theme_engine import ThemeEngine
from orchestrator.progress_tracker import ProgressTracker
from orchestrator.batch_runner import BatchRunner


class DashboardState:
    """Singleton state for the dashboard application."""

    def __init__(self):
        self.businesses: list[dict] = []
        self.spreadsheet_name: str = ""
        self.batch_task: asyncio.Task | None = None
        self.batch_runner: BatchRunner | None = None
        self.concurrency: int = DEFAULT_CONCURRENCY
        self.is_running: bool = False
        self.started_at: str | None = None
        self.settings: dict = {
            "github_token": bool(os.environ.get("GITHUB_TOKEN")),
            "github_auth": False,
            "claude_cli": False,
            "concurrency": DEFAULT_CONCURRENCY,
            "session_timeout": 1800,
        }
        self._check_claude_cli()
        self._check_github_auth()

    def _check_github_auth(self):
        """Check if gh CLI is authenticated (non-blocking best-effort)."""
        try:
            import subprocess
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True, timeout=5,
            )
            self.settings["github_auth"] = result.returncode == 0
        except Exception:
            self.settings["github_auth"] = False

    def _check_claude_cli(self):
        """Check if Claude Code CLI is available (non-blocking best-effort)."""
        try:
            import subprocess
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True, timeout=5,
            )
            self.settings["claude_cli"] = result.returncode == 0
        except Exception:
            self.settings["claude_cli"] = False

    # ── Spreadsheet ──────────────────────────────────────────────

    def load_spreadsheet(self, file_path: Path, count: int | None = None) -> int:
        """Load businesses from a spreadsheet file. Returns count loaded."""
        self.businesses = read_spreadsheet(file_path, count=count)
        self.spreadsheet_name = file_path.name
        return len(self.businesses)

    # ── Batch Control ────────────────────────────────────────────

    async def start_batch(
        self,
        count: int | None = None,
        concurrency: int | None = None,
    ) -> str:
        """Start a batch job. Returns status message."""
        if self.is_running:
            return "A batch is already running."
        if not self.businesses:
            return "No spreadsheet loaded."

        targets = self.businesses[:count] if count else self.businesses
        conc = min(concurrency or self.concurrency, MAX_CONCURRENCY)

        self.batch_runner = BatchRunner(concurrency=conc)
        self.is_running = True
        self.started_at = datetime.now(timezone.utc).isoformat()

        self.batch_task = asyncio.create_task(self._run_batch(targets))
        return f"Started building {len(targets)} sites (concurrency={conc})"

    async def _run_batch(self, targets: list[dict]):
        """Internal batch runner wrapper."""
        try:
            await self.batch_runner.run(targets)
        except Exception as e:
            import traceback
            traceback.print_exc()
        finally:
            self.is_running = False

    async def stop_batch(self) -> str:
        """Request graceful shutdown of the running batch."""
        if not self.is_running or not self.batch_runner:
            return "No batch is running."
        self.batch_runner._shutdown = True
        return "Shutdown requested — finishing current builds..."

    # ── Progress ─────────────────────────────────────────────────

    def get_progress(self) -> dict:
        """Read progress from JSON file."""
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE) as f:
                return json.load(f)
        return {}

    def get_stats(self) -> dict:
        """Get aggregate statistics."""
        progress = self.get_progress()
        total = len(progress)
        statuses = {}
        for entry in progress.values():
            s = entry.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1

        return {
            "total": total,
            "complete": statuses.get("complete", 0),
            "building": statuses.get("building", 0),
            "failed": statuses.get("failed", 0),
            "queued": statuses.get("queued", 0),
            "retrying": statuses.get("retrying", 0),
            "is_running": self.is_running,
            "started_at": self.started_at,
            "spreadsheet": self.spreadsheet_name,
            "businesses_loaded": len(self.businesses),
        }

    # ── Logs ─────────────────────────────────────────────────────

    def get_log_files(self) -> list[dict]:
        """List available log files."""
        if not LOGS_DIR.exists():
            return []
        logs = []
        for f in sorted(LOGS_DIR.glob("*.log")):
            logs.append({
                "name": f.stem,
                "file": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(
                    f.stat().st_mtime, timezone.utc
                ).isoformat(),
            })
        return logs

    def read_log(self, slug: str, tail: int = 100) -> list[str]:
        """Read the last N lines of a site log. Prefers live log if available."""
        # Try live log first (real-time streaming output)
        live_log = LOGS_DIR / f"{slug}.live.log"
        if live_log.exists() and live_log.stat().st_size > 0:
            lines = live_log.read_text().strip().split("\n")
            return lines[-tail:]

        # Fall back to structured log
        log_file = LOGS_DIR / f"{slug}.log"
        if not log_file.exists():
            return [f"No log file found for '{slug}'"]
        lines = log_file.read_text().strip().split("\n")
        return lines[-tail:]

    def get_live_activity(self) -> list[dict]:
        """Get recent activity across all building sites for the live feed."""
        progress = self.get_progress()
        activity = []
        for slug, data in progress.items():
            if data.get("status") in ("building", "retrying"):
                # Read last few lines from live log
                live_log = LOGS_DIR / f"{slug}.live.log"
                last_line = ""
                if live_log.exists():
                    try:
                        lines = live_log.read_text().strip().split("\n")
                        last_line = lines[-1] if lines else ""
                    except Exception:
                        pass
                activity.append({
                    "slug": slug,
                    "business_name": data.get("business_name", slug),
                    "phase": data.get("phase", ""),
                    "started_at": data.get("started_at", ""),
                    "last_output": last_line,
                })
        return activity

    # ── Deployed Sites ───────────────────────────────────────────

    def get_deployed_sites(self) -> list[dict]:
        """Get list of successfully deployed sites with URLs."""
        progress = self.get_progress()
        deployed = []
        for slug, data in progress.items():
            if data.get("status") == "complete":
                deployed.append({
                    "slug": slug,
                    "business_name": data.get("business_name", slug),
                    "github_url": data.get("github_url"),
                    "pages_url": data.get("pages_url"),
                    "completed_at": data.get("completed_at"),
                })
        return deployed

    # ── Retry ────────────────────────────────────────────────────

    async def retry_site(self, slug: str) -> str:
        """Retry a single failed site."""
        matching = [b for b in self.businesses if b.get("slug") == slug]
        if not matching:
            return f"Business '{slug}' not found in loaded data."

        runner = BatchRunner(concurrency=1)
        asyncio.create_task(runner.run(matching[:1]))
        return f"Retrying build for '{slug}'..."

    # ── Cleanup ──────────────────────────────────────────────────

    def clear_progress(self) -> str:
        """Reset progress file."""
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()
        return "Progress cleared."

    def clear_workspaces(self) -> str:
        """Remove all workspace directories."""
        if WORKSPACE_DIR.exists():
            for child in WORKSPACE_DIR.iterdir():
                if child.is_dir() and child.name != ".gitkeep":
                    shutil.rmtree(child, ignore_errors=True)
        return "Workspaces cleared."


# Singleton instance
state = DashboardState()
