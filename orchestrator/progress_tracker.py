"""Track progress of all site builds with a JSON file and Rich terminal dashboard."""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from orchestrator.config import PROGRESS_FILE, LOGS_DIR


class ProgressTracker:
    """Thread-safe progress tracker with JSON persistence and terminal display."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._progress: dict[str, dict] = {}
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE) as f:
                self._progress = json.load(f)

    def _save(self) -> None:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(self._progress, f, indent=2)

    async def init_site(self, slug: str, business_name: str) -> None:
        async with self._lock:
            self._progress[slug] = {
                "business_name": business_name,
                "status": "queued",
                "phase": "",
                "github_url": None,
                "pages_url": None,
                "started_at": None,
                "completed_at": None,
                "error": None,
                "retries": 0,
            }
            self._save()

    async def start_site(self, slug: str) -> None:
        async with self._lock:
            if slug in self._progress:
                self._progress[slug]["status"] = "building"
                self._progress[slug]["started_at"] = _now()
                self._save()

    async def update_phase(self, slug: str, phase: str) -> None:
        async with self._lock:
            if slug in self._progress:
                self._progress[slug]["phase"] = phase
                self._save()

    async def complete_site(
        self, slug: str, github_url: str | None = None, pages_url: str | None = None
    ) -> None:
        async with self._lock:
            if slug in self._progress:
                self._progress[slug]["status"] = "complete"
                self._progress[slug]["completed_at"] = _now()
                self._progress[slug]["github_url"] = github_url
                self._progress[slug]["pages_url"] = pages_url
                self._save()

    async def fail_site(self, slug: str, error: str) -> None:
        async with self._lock:
            if slug in self._progress:
                self._progress[slug]["status"] = "failed"
                self._progress[slug]["completed_at"] = _now()
                self._progress[slug]["error"] = error
                self._save()

    async def increment_retry(self, slug: str) -> int:
        async with self._lock:
            if slug in self._progress:
                self._progress[slug]["retries"] += 1
                self._progress[slug]["status"] = "retrying"
                self._save()
                return self._progress[slug]["retries"]
            return 0

    def get_summary(self) -> dict:
        """Get summary statistics."""
        total = len(self._progress)
        statuses = {}
        for entry in self._progress.values():
            s = entry["status"]
            statuses[s] = statuses.get(s, 0) + 1
        return {"total": total, **statuses}

    def print_dashboard(self) -> None:
        """Print a rich terminal dashboard of current progress."""
        try:
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title="Marketing Site Factory — Progress")

            table.add_column("Business", style="cyan")
            table.add_column("Status", style="bold")
            table.add_column("Phase")
            table.add_column("GitHub URL")
            table.add_column("Pages URL")
            table.add_column("Retries")

            status_colors = {
                "queued": "dim",
                "building": "yellow",
                "deploying": "blue",
                "complete": "green",
                "failed": "red",
                "retrying": "magenta",
            }

            for slug, data in self._progress.items():
                status = data["status"]
                style = status_colors.get(status, "white")
                table.add_row(
                    data.get("business_name", slug),
                    f"[{style}]{status}[/{style}]",
                    data.get("phase", ""),
                    data.get("github_url", "") or "—",
                    data.get("pages_url", "") or "—",
                    str(data.get("retries", 0)),
                )

            console.print(table)

            summary = self.get_summary()
            console.print(
                f"\nTotal: {summary.get('total', 0)} | "
                f"Complete: {summary.get('complete', 0)} | "
                f"Building: {summary.get('building', 0)} | "
                f"Failed: {summary.get('failed', 0)}"
            )
        except ImportError:
            # Fallback without rich
            print("\n=== Progress ===")
            for slug, data in self._progress.items():
                print(f"  {data.get('business_name', slug)}: {data['status']} ({data.get('phase', '')})")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
