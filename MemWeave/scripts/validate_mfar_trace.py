#!/usr/bin/env python3
"""Validate one MFAR trace JSON document against the versioned schema.

Install the optional validator dependency with:
    python -m pip install jsonschema

Examples:
    python MemWeave/scripts/validate_mfar_trace.py trace.json
    python MemWeave/scripts/validate_mfar_trace.py trace.json --online
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover - depends on local environment
    raise SystemExit(
        "Missing dependency 'jsonschema'. Install it with: "
        "python -m pip install jsonschema"
    ) from exc


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "mfar_trace.schema.json"
)


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read valid JSON from {path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="Path to an MFAR trace JSON file")
    parser.add_argument(
        "--online",
        action="store_true",
        help="Reject evaluation-only oracle labels in an online/inference trace",
    )
    args = parser.parse_args()

    schema = load_json(SCHEMA_PATH)
    trace = load_json(args.trace)

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(trace),
        key=lambda error: list(error.absolute_path),
    )

    if args.online and trace.get("oracle_labels") is not None:
        print(
            "ERROR: oracle_labels must be null in online/inference traces.",
            file=sys.stderr,
        )
        return 1

    if errors:
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            print(f"ERROR at {location}: {error.message}", file=sys.stderr)
        print(f"Invalid MFAR trace: {len(errors)} schema violation(s).", file=sys.stderr)
        return 1

    print(f"Valid MFAR trace: {args.trace}")
    if args.online:
        print("Online mode check passed: no oracle labels supplied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
