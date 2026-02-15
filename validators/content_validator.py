"""Validate content quality — no placeholders, all pages have real content."""

import re
from pathlib import Path

PLACEHOLDER_PATTERNS = [
    r"lorem ipsum",
    r"\[business.?name\]",
    r"\[your.?name\]",
    r"\[company.?name\]",
    r"\[phone\]",
    r"\[email\]",
    r"\[address\]",
    r"\[city\]",
    r"\[description\]",
    r"placeholder",
    r"TODO:",
    r"FIXME:",
    r"xxx",
]

REQUIRED_PAGES = [
    "src/app/page.tsx",        # Home
    "src/app/about/page.tsx",  # About
    "src/app/services/page.tsx",  # Services
    "src/app/contact/page.tsx",   # Contact
    "src/app/blog/page.tsx",      # Blog
    "src/app/layout.tsx",         # Root layout
]


def validate_content(workspace: Path) -> dict:
    """
    Check for placeholder text and content completeness.

    Returns:
        Dict with passed, score, issues, warnings.
    """
    issues = []
    warnings = []
    score = 100

    # Check required pages exist
    for rel_path in REQUIRED_PAGES:
        full_path = workspace / rel_path
        if not full_path.exists():
            issues.append(f"Missing page: {rel_path}")
            score -= 15

    # Scan all TSX/TS files for placeholder text
    src_dir = workspace / "src"
    if src_dir.exists():
        for ts_file in src_dir.rglob("*.tsx"):
            content = ts_file.read_text(errors="replace").lower()
            rel_path = ts_file.relative_to(workspace)

            for pattern in PLACEHOLDER_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(f"Placeholder text found in {rel_path}: matches '{pattern}'")
                    score -= 10
                    break  # One issue per file is enough

    # Check that home page has substantial content (at least 500 chars of JSX)
    home_page = workspace / "src" / "app" / "page.tsx"
    if home_page.exists():
        content = home_page.read_text(errors="replace")
        # Rough check: the return JSX should have real content
        if len(content) < 500:
            warnings.append("Home page seems too short — may lack content")
            score -= 5

    # Check contact page has form elements
    contact_page = workspace / "src" / "app" / "contact" / "page.tsx"
    if contact_page.exists():
        content = contact_page.read_text(errors="replace").lower()
        if "form" not in content and "input" not in content:
            warnings.append("Contact page may be missing a contact form")
            score -= 5

    score = max(0, score)
    passed = score >= 70 and not any("Missing page" in i for i in issues[:3])

    return {
        "passed": passed,
        "score": score,
        "issues": issues,
        "warnings": warnings,
    }
