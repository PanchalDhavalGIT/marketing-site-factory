"""Read and validate business listing spreadsheets (CSV/Excel)."""

from pathlib import Path

import pandas as pd

from orchestrator.config import REQUIRED_COLUMNS, OPTIONAL_COLUMNS


def read_spreadsheet(path: str | Path, count: int | None = None) -> list[dict]:
    """
    Read a spreadsheet and return a list of business data dicts.

    Args:
        path: Path to CSV or Excel file.
        count: Optional limit on number of rows to return.

    Returns:
        List of dicts, one per business.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If required columns are missing.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Spreadsheet not found: {path}")

    if path.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    elif path.suffix == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .csv or .xlsx")

    # Normalize column names: strip whitespace, lowercase, underscores
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    # Validate required columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. "
            f"Found: {list(df.columns)}. "
            f"Required: {REQUIRED_COLUMNS}"
        )

    # Limit rows
    if count is not None:
        df = df.head(count)

    # Drop fully empty rows
    df = df.dropna(subset=REQUIRED_COLUMNS)

    # Convert to list of dicts, keeping only known columns
    all_columns = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
    present_columns = [c for c in all_columns if c in df.columns]
    df = df[present_columns]

    # Fill NaN with empty string
    df = df.fillna("")

    records = df.to_dict("records")

    # Generate slug for each record
    for record in records:
        record["slug"] = _slugify(record["business_name"])

    return records


def _slugify(name: str) -> str:
    """Convert business name to URL-safe slug."""
    import re
    slug = name.lower().strip()
    slug = re.sub(r"['\"]", "", slug)           # Remove quotes
    slug = re.sub(r"[^a-z0-9]+", "-", slug)     # Replace non-alphanum with hyphens
    slug = slug.strip("-")                        # Trim leading/trailing hyphens
    return slug
