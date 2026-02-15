"""Validate that a Next.js site builds successfully."""

import asyncio
import json
from pathlib import Path


async def validate_build(workspace: Path) -> dict:
    """
    Run npm build and check for success.

    Returns:
        Dict with passed, error fields.
    """
    package_json = workspace / "package.json"
    if not package_json.exists():
        return {
            "passed": False,
            "error": "No package.json found — site was not scaffolded",
        }

    process = await asyncio.create_subprocess_exec(
        "npm", "run", "build",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(workspace),
    )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
    except asyncio.TimeoutError:
        process.kill()
        return {"passed": False, "error": "Build timed out after 120 seconds"}

    if process.returncode == 0:
        return {"passed": True, "error": None}
    else:
        error_output = stderr.decode("utf-8", errors="replace")[:2000]
        return {"passed": False, "error": error_output}
