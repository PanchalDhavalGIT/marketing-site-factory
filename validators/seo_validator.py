"""Validate SEO completeness of a built Next.js site."""

import re
from pathlib import Path


def validate_seo(workspace: Path) -> dict:
    """
    Check for required SEO elements across all pages.

    Returns:
        Dict with passed, score, issues, warnings.
    """
    issues = []
    warnings = []
    score = 100

    app_dir = workspace / "src" / "app"
    if not app_dir.exists():
        return {
            "passed": False,
            "score": 0,
            "issues": ["src/app/ directory not found"],
            "warnings": [],
        }

    # Check for metadata exports in page files
    page_files = list(app_dir.rglob("page.tsx")) + list(app_dir.rglob("page.ts"))
    pages_with_metadata = 0

    for page_file in page_files:
        content = page_file.read_text(errors="replace")
        if "metadata" in content and ("title" in content):
            pages_with_metadata += 1
        else:
            rel_path = page_file.relative_to(workspace)
            issues.append(f"Missing metadata export in {rel_path}")
            score -= 10

    # Check for Schema.org JSON-LD in layout
    layout_file = app_dir / "layout.tsx"
    if layout_file.exists():
        layout_content = layout_file.read_text(errors="replace")
        if "schema.org" in layout_content.lower() or "application/ld+json" in layout_content:
            pass  # Good
        else:
            warnings.append("No Schema.org JSON-LD found in root layout")
            score -= 5

    # Check sitemap.xml
    sitemap = workspace / "public" / "sitemap.xml"
    if not sitemap.exists():
        warnings.append("Missing public/sitemap.xml")
        score -= 5

    # Check robots.txt
    robots = workspace / "public" / "robots.txt"
    if not robots.exists():
        warnings.append("Missing public/robots.txt")
        score -= 5

    score = max(0, score)
    passed = score >= 70 and not any("Missing metadata" in i for i in issues)

    return {
        "passed": passed,
        "score": score,
        "issues": issues,
        "warnings": warnings,
        "pages_checked": len(page_files),
        "pages_with_metadata": pages_with_metadata,
    }
