"""Workspace isolation — creates and manages per-site working directories."""

import json
import os
import shutil
from pathlib import Path

from orchestrator.config import (
    WORKSPACE_DIR,
    CLAUDE_DIR,
    SKILLS_DIR,
    AGENTS_DIR,
)


def create_workspace(slug: str, business_data: dict, theme: dict) -> Path:
    """
    Create an isolated workspace directory for a site build.

    Creates:
      workspace/{slug}/
        ├── brief.json          (business data + theme)
        ├── .claude/
        │   ├── skills/ → symlink to shared skills
        │   ├── agents/ → symlink to shared agents
        │   └── settings.json   (copy of project settings)

    Returns:
        Path to the workspace directory.
    """
    workspace = WORKSPACE_DIR / slug
    workspace.mkdir(parents=True, exist_ok=True)

    # Write brief.json with business data and theme
    brief = {
        "business": business_data,
        "theme": theme,
    }
    with open(workspace / "brief.json", "w") as f:
        json.dump(brief, f, indent=2)

    # Create .claude directory structure in workspace
    claude_dir = workspace / ".claude"
    claude_dir.mkdir(exist_ok=True)

    # Symlink skills and agents directories
    skills_link = claude_dir / "skills"
    if not skills_link.exists():
        skills_link.symlink_to(SKILLS_DIR.resolve())

    agents_link = claude_dir / "agents"
    if not agents_link.exists():
        agents_link.symlink_to(AGENTS_DIR.resolve())

    # Copy settings.json (hooks need to be in the workspace)
    settings_src = CLAUDE_DIR / "settings.json"
    if settings_src.exists():
        shutil.copy2(settings_src, claude_dir / "settings.json")

    # Copy hooks directory
    hooks_src = CLAUDE_DIR / "hooks"
    hooks_dst = claude_dir / "hooks"
    if hooks_src.exists() and not hooks_dst.exists():
        shutil.copytree(hooks_src, hooks_dst)

    return workspace


def cleanup_workspace(slug: str, keep_results: bool = True) -> None:
    """
    Clean up a workspace after deployment.

    Args:
        slug: Business slug.
        keep_results: If True, keep status.json and deploy-result.json.
    """
    workspace = WORKSPACE_DIR / slug
    if not workspace.exists():
        return

    if keep_results:
        # Move key result files to logs before cleanup
        result_files = [
            "status.json",
            "deploy-result.json",
            "validation-result.json",
            "cx-review.json",
        ]
        from orchestrator.config import LOGS_DIR
        results_dir = LOGS_DIR / slug
        results_dir.mkdir(parents=True, exist_ok=True)
        for fname in result_files:
            src = workspace / fname
            if src.exists():
                shutil.copy2(src, results_dir / fname)

    # Remove the workspace
    shutil.rmtree(workspace, ignore_errors=True)


def get_workspace_path(slug: str) -> Path:
    """Get the workspace path for a site."""
    return WORKSPACE_DIR / slug
