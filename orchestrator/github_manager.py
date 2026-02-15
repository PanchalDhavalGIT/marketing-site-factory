"""GitHub repository management via gh CLI."""

import asyncio
import json
import random
import string

from orchestrator.logger import get_main_logger

logger = get_main_logger()


async def create_repo(slug: str, description: str = "") -> dict:
    """
    Create a GitHub repository for a marketing site.

    Args:
        slug: Business slug (repo name will be marketing-{slug}).
        description: Repository description.

    Returns:
        Dict with repo_url, status.
    """
    repo_name = f"marketing-{slug}"

    # Check if repo exists
    exists = await _repo_exists(repo_name)
    if exists:
        suffix = "".join(random.choices(string.digits, k=4))
        repo_name = f"marketing-{slug}-{suffix}"
        logger.warning(f"Repo already exists, using: {repo_name}")

    cmd = [
        "gh", "repo", "create", repo_name,
        "--public",
        "--description", description or f"Marketing site for {slug}",
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        url = stdout.decode().strip()
        logger.info(f"Created GitHub repo: {url}")
        return {"repo_name": repo_name, "repo_url": url, "status": "success"}
    else:
        error = stderr.decode().strip()
        logger.error(f"Failed to create repo {repo_name}: {error}")
        return {"repo_name": repo_name, "repo_url": None, "status": "failed", "error": error}


async def _repo_exists(repo_name: str) -> bool:
    """Check if a GitHub repo already exists."""
    process = await asyncio.create_subprocess_exec(
        "gh", "repo", "view", repo_name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await process.communicate()
    return process.returncode == 0
