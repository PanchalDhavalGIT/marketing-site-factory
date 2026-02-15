"""Batch execution engine — runs N site builds concurrently with asyncio."""

import asyncio
import signal
import sys
from pathlib import Path

from orchestrator.config import MAX_RETRIES, RETRY_BACKOFF_BASE, DEFAULT_SESSION_TIMEOUT
from orchestrator.context_manager import create_workspace, cleanup_workspace
from orchestrator.logger import get_main_logger, get_site_logger
from orchestrator.progress_tracker import ProgressTracker
from orchestrator.session_manager import launch_session, build_pm_prompt, SessionResult
from orchestrator.theme_engine import ThemeEngine

logger = get_main_logger()


class BatchRunner:
    """Runs multiple site builds concurrently with controlled parallelism."""

    def __init__(self, concurrency: int, dry_run: bool = False):
        self.concurrency = concurrency
        self.dry_run = dry_run
        self.semaphore = asyncio.Semaphore(concurrency)
        self.theme_engine = ThemeEngine()
        self.progress = ProgressTracker()
        self._shutdown = False

    async def run(self, businesses: list[dict]) -> None:
        """
        Run site generation for all businesses.

        Args:
            businesses: List of business data dicts from spreadsheet_reader.
        """
        logger.info(f"Starting batch: {len(businesses)} sites, concurrency={self.concurrency}")

        if self.dry_run:
            await self._dry_run(businesses)
            return

        # Handle graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._handle_shutdown)

        # Initialize progress for all sites
        for biz in businesses:
            await self.progress.init_site(biz["slug"], biz["business_name"])

        # Launch all tasks
        tasks = [self._build_site(biz) for biz in businesses]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Report results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                slug = businesses[i]["slug"]
                logger.error(f"Unexpected error for {slug}: {result}")
                await self.progress.fail_site(slug, str(result))

        self.progress.print_dashboard()
        logger.info("Batch complete")

    async def _build_site(self, business: dict) -> None:
        """Build a single site with semaphore-controlled concurrency."""
        slug = business["slug"]
        site_logger = get_site_logger(slug)

        async with self.semaphore:
            if self._shutdown:
                site_logger.info("Shutdown requested — skipping")
                return

            site_logger.info(f"Starting build for: {business['business_name']}")
            await self.progress.start_site(slug)

            # Assign unique theme
            industry = business.get("industry", "default")
            theme = await self.theme_engine.assign(industry, business["business_name"])
            await self.progress.update_phase(slug, "theme_assigned")
            site_logger.info(f"Assigned theme: {theme['id']}")

            # Create isolated workspace
            workspace = create_workspace(slug, business, theme)
            await self.progress.update_phase(slug, "workspace_created")

            # Build PM prompt
            prompt = build_pm_prompt(business, theme)

            # Execute with retry logic
            retry_count = 0
            success = False

            # Progress callback for real-time phase updates from Claude output
            async def _on_phase(s, phase):
                await self.progress.update_phase(s, phase)

            while retry_count <= MAX_RETRIES and not self._shutdown:
                await self.progress.update_phase(slug, f"claude_session (attempt {retry_count + 1})")
                result = await launch_session(
                    workspace=workspace,
                    prompt=prompt,
                    timeout=DEFAULT_SESSION_TIMEOUT,
                    site_slug=slug,
                    progress_callback=_on_phase,
                )

                if result.success:
                    success = True
                    break

                if result.timed_out or not result.success:
                    retry_count = await self.progress.increment_retry(slug)
                    if retry_count <= MAX_RETRIES:
                        backoff = RETRY_BACKOFF_BASE * (2 ** (retry_count - 1))
                        site_logger.warning(
                            f"Retry {retry_count}/{MAX_RETRIES} after {backoff}s: {result.error[:200]}"
                        )
                        await asyncio.sleep(backoff)
                    else:
                        break

            # Release theme
            await self.theme_engine.release(theme["id"])

            if success:
                # Try to read deploy results
                github_url, pages_url = _read_deploy_results(workspace)
                await self.progress.complete_site(slug, github_url, pages_url)
                site_logger.info(f"Build complete: github={github_url}, pages={pages_url}")
            else:
                await self.progress.fail_site(slug, result.error[:500] if result else "Unknown error")
                site_logger.error(f"Build failed after {retry_count} retries")

            # Cleanup workspace (keep result files)
            cleanup_workspace(slug, keep_results=True)

    async def _dry_run(self, businesses: list[dict]) -> None:
        """Preview what would happen without actually building."""
        logger.info("=== DRY RUN MODE ===")

        for biz in businesses:
            industry = biz.get("industry", "default")
            theme = await self.theme_engine.assign(industry, biz["business_name"])

            logger.info(
                f"  [{biz['slug']}] "
                f"{biz['business_name']} ({industry}) "
                f"→ theme: {theme['name']} ({theme['id']})"
            )

            await self.theme_engine.release(theme["id"])

        logger.info(f"\nWould build {len(businesses)} sites with concurrency={self.concurrency}")
        logger.info("=== END DRY RUN ===")

    def _handle_shutdown(self) -> None:
        """Handle graceful shutdown signal."""
        logger.warning("Shutdown signal received — finishing current builds...")
        self._shutdown = True


def _read_deploy_results(workspace: Path) -> tuple[str | None, str | None]:
    """Read deployment result files from workspace. Returns (github_url, pages_url)."""
    github_url = None
    pages_url = None

    status_file = workspace / "status.json"
    if status_file.exists():
        import json
        with open(status_file) as f:
            data = json.load(f)
            github_url = data.get("github_url")
            pages_url = data.get("pages_url")

    deploy_file = workspace / "deploy-result.json"
    if deploy_file.exists():
        import json
        with open(deploy_file) as f:
            data = json.load(f)
            github_url = github_url or data.get("github_url") or data.get("repo_url")
            pages_url = pages_url or data.get("pages_url")

    return github_url, pages_url
