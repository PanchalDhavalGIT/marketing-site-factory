"""Manages Claude Code CLI session lifecycle — launch, monitor, timeout, retry."""

import asyncio
import json
import os
import time
from pathlib import Path

from orchestrator.config import (
    CLAUDE_CMD,
    CLAUDE_MAX_TURNS,
    CLAUDE_OUTPUT_FORMAT,
    DEFAULT_SESSION_TIMEOUT,
    LOGS_DIR,
)
from orchestrator.logger import get_site_logger


class SessionResult:
    """Result of a Claude Code session."""

    def __init__(
        self,
        success: bool,
        output: str = "",
        error: str = "",
        timed_out: bool = False,
    ):
        self.success = success
        self.output = output
        self.error = error
        self.timed_out = timed_out


async def launch_session(
    workspace: Path,
    prompt: str,
    timeout: int = DEFAULT_SESSION_TIMEOUT,
    site_slug: str = "",
    progress_callback=None,
) -> SessionResult:
    """
    Launch a Claude Code CLI session in the given workspace.
    Streams stdout to log file in real-time for dashboard visibility.

    Args:
        workspace: Path to the isolated workspace directory.
        prompt: The prompt to send to Claude Code.
        timeout: Maximum seconds before killing the session.
        site_slug: For logging purposes.
        progress_callback: async callable(slug, phase_msg) for live updates.

    Returns:
        SessionResult with success/failure and output.
    """
    logger = get_site_logger(site_slug or workspace.name)
    slug = site_slug or workspace.name

    cmd = [
        CLAUDE_CMD,
        "-p",  # Print mode (non-interactive)
        prompt,
        "--output-format", CLAUDE_OUTPUT_FORMAT,
        "--max-turns", str(CLAUDE_MAX_TURNS),
        "--dangerously-skip-permissions",
    ]

    env = os.environ.copy()
    env["HOME"] = os.environ.get("HOME", "")

    logger.info(f"Launching Claude session in {workspace}")

    # Prepare live log file for streaming
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    live_log = LOGS_DIR / f"{slug}.live.log"

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(workspace),
            env=env,
        )

        stdout_lines = []
        stderr_lines = []
        start_time = time.time()

        async def read_stream(stream, collector, is_stderr=False):
            """Read stream line-by-line and write to log in real-time."""
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").rstrip()
                collector.append(decoded)

                # Write to live log file for dashboard
                with open(live_log, "a") as f:
                    elapsed = int(time.time() - start_time)
                    prefix = "ERR" if is_stderr else "OUT"
                    f.write(f"[{elapsed:>4}s] [{prefix}] {decoded}\n")

                # Log to structured log
                if is_stderr:
                    logger.warning(f"stderr: {decoded[:300]}")
                else:
                    logger.info(f"stdout: {decoded[:300]}")

                # Detect phase changes from output and fire callback
                if progress_callback and not is_stderr:
                    phase = _detect_phase(decoded)
                    if phase:
                        await progress_callback(slug, phase)

        try:
            await asyncio.wait_for(
                asyncio.gather(
                    read_stream(process.stdout, stdout_lines),
                    read_stream(process.stderr, stderr_lines, is_stderr=True),
                    process.wait(),
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            elapsed = int(time.time() - start_time)
            logger.warning(f"Session timed out after {elapsed}s — killing process")
            process.kill()
            await process.wait()
            return SessionResult(
                success=False,
                error=f"Session timed out after {timeout} seconds",
                timed_out=True,
            )

        stdout = "\n".join(stdout_lines)
        stderr = "\n".join(stderr_lines)
        elapsed = int(time.time() - start_time)

        if process.returncode == 0:
            logger.info(f"Session completed successfully in {elapsed}s")
            return SessionResult(success=True, output=stdout)
        else:
            logger.error(f"Session failed (exit {process.returncode}) after {elapsed}s: {stderr[:500]}")
            return SessionResult(
                success=False,
                output=stdout,
                error=stderr or f"Exit code: {process.returncode}",
            )

    except FileNotFoundError:
        error = f"Claude CLI not found at '{CLAUDE_CMD}'. Is it installed?"
        logger.error(error)
        return SessionResult(success=False, error=error)
    except Exception as e:
        error = f"Unexpected error launching session: {e}"
        logger.error(error)
        return SessionResult(success=False, error=error)


def _detect_phase(line: str) -> str | None:
    """Detect which agent/phase is running from Claude's output."""
    lower = line.lower()

    # Detect agent launches from Task tool usage
    phase_keywords = {
        "researcher": "researching",
        "brand-identity": "branding",
        "brand identity": "branding",
        "ux-architect": "ux_design",
        "ux architect": "ux_design",
        "copywriter": "copywriting",
        "ui-designer": "ui_design",
        "ui designer": "ui_design",
        "frontend-dev": "frontend_build",
        "frontend dev": "frontend_build",
        "create-next-app": "frontend_build",
        "seo-specialist": "seo_optimization",
        "seo specialist": "seo_optimization",
        "cx-analyst": "cx_review",
        "cx analyst": "cx_review",
        "site-validator": "validation",
        "site validator": "validation",
        "deployer": "deploying",
        "gh repo create": "github_push",
        "deploy-pages": "github_pages",
        "npm run build": "building",
        "npx create-next-app": "scaffolding",
    }

    for keyword, phase in phase_keywords.items():
        if keyword in lower:
            return phase
    return None


def build_pm_prompt(business_data: dict, theme: dict) -> str:
    """
    Build the prompt for the Project Manager agent.

    The PM agent will read brief.json for full details, but we give it
    a summary in the prompt to set context.
    """
    name = business_data.get("business_name", "Unknown")
    industry = business_data.get("industry", "general")
    description = business_data.get("description", "")
    services = business_data.get("services", "")

    prompt = f"""You are the Project Manager agent. Build a complete marketing website for this business:

Business: {name}
Industry: {industry}
Description: {description}
Services: {services}
Assigned Theme: {theme.get('name', 'Modern Minimal')} ({theme.get('id', 'modern-minimal')})

Your full brief is in brief.json in the current directory. Follow the project-manager agent workflow exactly:

1. Read brief.json for complete business data and theme
2. Launch sub-agents in sequence: researcher → brand-identity → ux-architect → copywriter → ui-designer → frontend-dev → seo-specialist → cx-analyst → site-validator → deployer
3. Pass outputs between phases (each agent writes JSON files that the next reads)
4. The frontend-dev agent builds the actual Next.js site
5. Validate and deploy

Build a UNIQUE site — do not reuse layouts or copy from other sites. The theme in brief.json is your starting point for visual identity.

Write status.json when complete with final URLs and scores."""

    return prompt
