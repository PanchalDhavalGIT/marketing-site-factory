"""
Marketing Site Factory — Main Entry Point.

Usage:
    python -m orchestrator.main --spreadsheet data/businesses.csv --count 5 --concurrency 5
    python -m orchestrator.main --spreadsheet data/businesses.csv --count 50 --concurrency 10 --dry-run
"""

import argparse
import asyncio
import sys

from orchestrator.config import DEFAULT_CONCURRENCY, MAX_CONCURRENCY, validate_env
from orchestrator.logger import get_main_logger
from orchestrator.spreadsheet_reader import read_spreadsheet
from orchestrator.batch_runner import BatchRunner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Marketing Site Factory — Generate marketing websites at scale"
    )
    parser.add_argument(
        "--spreadsheet", "-s",
        required=True,
        help="Path to CSV or Excel file with business data",
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=None,
        help="Number of businesses to process (default: all)",
    )
    parser.add_argument(
        "--concurrency", "-c",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Max concurrent builds (default: {DEFAULT_CONCURRENCY}, max: {MAX_CONCURRENCY})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview theme assignments without building",
    )
    return parser.parse_args()


def main() -> None:
    logger = get_main_logger()
    args = parse_args()

    logger.info("=== Marketing Site Factory ===")

    # Check environment
    warnings = validate_env()
    for w in warnings:
        logger.warning(w)

    if not args.dry_run and warnings:
        logger.error("Fix environment warnings above before running (or use --dry-run)")
        sys.exit(1)

    # Validate concurrency
    concurrency = min(args.concurrency, MAX_CONCURRENCY)
    if concurrency != args.concurrency:
        logger.warning(f"Concurrency capped at {MAX_CONCURRENCY}")

    # Read spreadsheet
    try:
        businesses = read_spreadsheet(args.spreadsheet, count=args.count)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)

    if not businesses:
        logger.error("No valid business entries found in spreadsheet")
        sys.exit(1)

    logger.info(f"Loaded {len(businesses)} businesses from {args.spreadsheet}")

    # Run batch
    runner = BatchRunner(concurrency=concurrency, dry_run=args.dry_run)
    asyncio.run(runner.run(businesses))


if __name__ == "__main__":
    main()
