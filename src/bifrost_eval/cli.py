"""CLI for bifrost-eval."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    """Entry point for the bifrost-eval CLI."""
    parser = argparse.ArgumentParser(
        prog="bifrost-eval",
        description="MCP pipeline evaluation toolkit",
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    subparsers = parser.add_subparsers(dest="command")

    # validate command. Running a suite requires a PipelineExecutor, which only
    # exists in Python code — so evaluation runs live in the Python API, and the
    # CLI only offers what it can actually do.
    validate_parser = subparsers.add_parser("validate", help="Validate a suite file")
    validate_parser.add_argument("suite_file", type=str, help="Path to evaluation suite JSON file")

    args = parser.parse_args(argv)

    if args.version:
        from bifrost_eval import __version__

        print(f"bifrost-eval {__version__}")
        return 0

    if args.command == "validate":
        return _cmd_validate(args.suite_file)

    parser.print_help()
    return 0


def _cmd_validate(suite_file: str) -> int:
    """Validate a suite JSON file."""
    path = Path(suite_file)
    if not path.exists():
        print(f"Error: File not found: {suite_file}")
        return 1

    try:
        data: Any = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"Error: Invalid JSON: {exc}")
        return 1

    from bifrost_eval.models.evaluation import EvalSuite

    try:
        suite = EvalSuite.model_validate(data)
    except Exception as exc:
        print(f"Error: Invalid suite format: {exc}")
        return 1

    print(f"Valid suite: {suite.name}")
    print(f"  Scenarios: {len(suite.scenarios)}")
    print(f"  Tags: {suite.tags}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
