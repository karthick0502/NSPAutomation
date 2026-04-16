"""
CLI: extract structured data from a sample enquiry email.

Usage:
  set OPENAI_API_KEY in .env or environment
  python run.py sample_emails/enquiry_01.txt
  python run.py sample_emails/enquiry_01.txt --image sample_attachments/sketch.png

In Git Bash, use forward slashes only (backslashes in paths are interpreted as escapes).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Allow running without installing the package
_ROOT = Path(__file__).resolve().parent
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from nsp_automation.logging_config import configure_logging
from nsp_automation.pipeline import result_to_json, run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NSP enquiry email to structured JSON",
    )
    parser.add_argument("email_file", type=Path, help="Path to .txt or .eml enquiry")
    parser.add_argument(
        "--image",
        "-i",
        action="append",
        dest="images",
        default=None,
        type=Path,
        help="Optional image path (repeat for multiple). Sent to vision model.",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: LOG_LEVEL env or INFO). Logs go to stderr; JSON to stdout.",
    )
    args = parser.parse_args()
    configure_logging(level=args.log_level)
    logger.info("Starting extraction for %s", args.email_file.resolve())
    if not args.email_file.is_file():
        print(f"File not found: {args.email_file}", file=sys.stderr)
        sys.exit(1)
    imgs = list(args.images) if args.images else None
    if imgs:
        for p in imgs:
            if not p.is_file():
                print(f"Image not found: {p}", file=sys.stderr)
                sys.exit(1)
    result = run_pipeline(args.email_file, attachment_paths=imgs)
    logger.info("Writing JSON to stdout")
    print(result_to_json(result))


if __name__ == "__main__":
    main()
