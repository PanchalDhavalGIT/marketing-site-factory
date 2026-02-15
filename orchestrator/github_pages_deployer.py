"""GitHub Pages deployment automation — replaces Vercel deployer."""

import asyncio
import os
from pathlib import Path

from orchestrator.config import GITHUB_TOKEN
from orchestrator.logger import get_main_logger

logger = get_main_logger()

DEPLOY_WORKFLOW = """name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: false
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-pages-artifact@v3
        with:
          path: out
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
"""


async def deploy(workspace_path: str, site_slug: str, repo_name: str) -> dict:
    """
    Deploy a static Next.js site to GitHub Pages.

    Args:
        workspace_path: Path to the built site.
        site_slug: For logging.
        repo_name: GitHub repo name (e.g., marketing-joes-pizza).

    Returns:
        Dict with pages_url, github_url, status.
    """
    token = GITHUB_TOKEN or os.environ.get("GITHUB_TOKEN", "")

    # 1. Ensure static export config
    await _ensure_static_export(workspace_path)

    # 2. Build
    build_result = await _run_build(workspace_path)
    if not build_result["success"]:
        return {
            "pages_url": None,
            "github_url": None,
            "status": "failed",
            "error": f"Build failed: {build_result['error']}",
        }

    # 3. Add GitHub Actions workflow
    workflow_dir = Path(workspace_path) / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "deploy.yml").write_text(DEPLOY_WORKFLOW)

    # 4. Commit and push workflow
    await _run_cmd(["git", "add", ".github/workflows/deploy.yml"], workspace_path)
    await _run_cmd(
        ["git", "commit", "-m", "Add GitHub Pages deployment workflow"],
        workspace_path,
    )
    push_result = await _run_cmd(["git", "push"], workspace_path)
    if not push_result["success"]:
        logger.warning(f"Push failed for {site_slug}: {push_result.get('error', '')}")

    # 5. Enable GitHub Pages via API
    owner = await _get_gh_owner()
    if owner:
        await _run_cmd(
            ["gh", "api", f"repos/{owner}/{repo_name}/pages",
             "-X", "POST", "-f", "build_type=workflow"],
            workspace_path,
        )

        pages_url = f"https://{owner}.github.io/{repo_name}/"
        github_url = f"https://github.com/{owner}/{repo_name}"

        logger.info(f"Deployed {site_slug}: {pages_url}")
        return {
            "pages_url": pages_url,
            "github_url": github_url,
            "status": "success",
        }

    return {
        "pages_url": None,
        "github_url": None,
        "status": "failed",
        "error": "Could not determine GitHub owner",
    }


async def _ensure_static_export(workspace_path: str) -> None:
    """Ensure next.config has output: 'export' for static generation."""
    ws = Path(workspace_path)

    for config_name in ["next.config.mjs", "next.config.ts", "next.config.js"]:
        config_path = ws / config_name
        if config_path.exists():
            content = config_path.read_text()
            if "output" not in content:
                # Add static export config
                content = content.replace(
                    "const nextConfig",
                    "const nextConfig"
                )
                if "output:" not in content and "output :" not in content:
                    content = content.replace(
                        "{}", '{\n  output: "export",\n  images: { unoptimized: true },\n}'
                    )
                    if "output" not in content:
                        # Fallback: insert after first {
                        content = content.replace(
                            "= {",
                            '= {\n  output: "export",\n  images: { unoptimized: true },',
                            1,
                        )
                    config_path.write_text(content)
            return

    # No config found — create one
    (ws / "next.config.mjs").write_text(
        '/** @type {import("next").NextConfig} */\n'
        "const nextConfig = {\n"
        '  output: "export",\n'
        "  images: { unoptimized: true },\n"
        "};\n\n"
        "export default nextConfig;\n"
    )


async def _run_build(workspace_path: str) -> dict:
    """Run npm build in the workspace."""
    process = await asyncio.create_subprocess_exec(
        "npm", "run", "build",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workspace_path,
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        return {"success": True}
    else:
        return {"success": False, "error": stderr.decode()[:1000]}


async def _run_cmd(cmd: list[str], cwd: str) -> dict:
    """Run a shell command and return success/error."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout, stderr = await process.communicate()
    return {
        "success": process.returncode == 0,
        "stdout": stdout.decode().strip(),
        "error": stderr.decode().strip(),
    }


async def _get_gh_owner() -> str | None:
    """Get the authenticated GitHub username."""
    process = await asyncio.create_subprocess_exec(
        "gh", "api", "user", "--jq", ".login",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()
    if process.returncode == 0:
        return stdout.decode().strip()
    return None
