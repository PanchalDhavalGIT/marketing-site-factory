"""Manages Claude Code CLI session lifecycle — launch, monitor, timeout, retry."""

import asyncio
import json
import os
from pathlib import Path

from orchestrator.config import (
    CLAUDE_CMD,
    CLAUDE_MAX_TURNS,
    CLAUDE_OUTPUT_FORMAT,
    DEFAULT_SESSION_TIMEOUT,
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
) -> SessionResult:
    """
    Launch a Claude Code CLI session in the given workspace.

    Args:
        workspace: Path to the isolated workspace directory.
        prompt: The prompt to send to Claude Code.
        timeout: Maximum seconds before killing the session.
        site_slug: For logging purposes.

    Returns:
        SessionResult with success/failure and output.
    """
    logger = get_site_logger(site_slug or workspace.name)

    cmd = [
        CLAUDE_CMD,
        "-p",  # Print mode (non-interactive)
        prompt,
        "--output-format", CLAUDE_OUTPUT_FORMAT,
        "--max-turns", str(CLAUDE_MAX_TURNS),
        "--dangerously-skip-permissions",
    ]

    env = os.environ.copy()
    # Ensure workspace has access to necessary tools
    env["HOME"] = os.environ.get("HOME", "")

    logger.info(f"Launching Claude session in {workspace}")
    logger.debug(f"Command: {' '.join(cmd)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(workspace),
            env=env,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Session timed out after {timeout}s — killing process")
            process.kill()
            await process.wait()
            return SessionResult(
                success=False,
                error=f"Session timed out after {timeout} seconds",
                timed_out=True,
            )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        if process.returncode == 0:
            logger.info("Session completed successfully")
            return SessionResult(success=True, output=stdout)
        else:
            logger.error(f"Session failed (exit code {process.returncode}): {stderr[:500]}")
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
