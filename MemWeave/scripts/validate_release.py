#!/usr/bin/env python3
"""Validate the committed MemWeave aggregate release artifacts.

This checks internal consistency only. It does not rerun model training,
reconstruct missing per-question outputs, or validate the benchmark source data.
Uses only the Python standard library.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def close(a: float, b: float, *, tol: float = 1e-8) -> bool:
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results" / "final_locked_test",
        help="Directory containing run_manifest.json, paired_test_audit.json, and question_type_breakdown.csv",
    )
    args = parser.parse_args()
    root = args.results_dir

    required = [
        root / "run_manifest.json",
        root / "paired_test_audit.json",
        root / "question_type_breakdown.csv",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        print("FAIL: missing required release artifacts:")
        for path in missing:
            print(f"  - {path}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    manifest = load_json(required[0])
    audit = load_json(required[1])

    m_test = manifest.get("primary_test", {})
    a_test = audit.get("test_metrics", {})
    n = int(audit.get("test_questions", 0))

    if n <= 0:
        errors.append("test_questions must be a positive integer")
    if int(m_test.get("n", -1)) != n:
        errors.append("run manifest primary_test.n disagrees with paired audit test_questions")

    metric_pairs = [
        ("baseline_budgeted_evidence_recall", "baseline_budgeted_evidence_recall"),
        ("role_aware_budgeted_evidence_recall", "role_aware_budgeted_evidence_recall"),
        ("paired_gain", "paired_mean_gain"),
    ]
    for manifest_key, audit_key in metric_pairs:
        if manifest_key not in m_test or audit_key not in a_test:
            errors.append(f"missing metric: {manifest_key} / {audit_key}")
        elif not close(m_test[manifest_key], a_test[audit_key]):
            errors.append(f"metric mismatch: manifest.{manifest_key} vs audit.{audit_key}")

    baseline = float(a_test.get("baseline_budgeted_evidence_recall", float("nan")))
    role_aware = float(a_test.get("role_aware_budgeted_evidence_recall", float("nan")))
    gain = float(a_test.get("paired_mean_gain", float("nan")))
    if not all(math.isfinite(x) for x in (baseline, role_aware, gain)):
        errors.append("primary metrics must be finite")
    elif not close(role_aware - baseline, gain):
        errors.append("paired gain does not equal role-aware recall minus baseline recall")

    ci = a_test.get("paired_bootstrap_95_ci", [])
    if len(ci) != 2 or not (0 <= float(ci[0]) <= float(ci[1]) <= 1):
        errors.append("paired bootstrap CI must contain two ordered values in [0, 1]")
    elif not (float(ci[0]) <= gain <= float(ci[1])):
        errors.append("paired gain is outside its reported bootstrap CI")

    with required[2].open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        errors.append("question_type_breakdown.csv has no data rows")
    else:
        required_columns = {
            "question_type", "n", "baseline_recall", "role_aware_recall",
            "absolute_gain", "ci_low", "ci_high", "sign_test_p_holm",
        }
        actual_columns = set(rows[0])
        absent = sorted(required_columns - actual_columns)
        if absent:
            errors.append("question-type CSV missing columns: " + ", ".join(absent))
        else:
            try:
                total_n = sum(int(row["n"]) for row in rows)
                if total_n != n:
                    errors.append(f"question-type sample counts sum to {total_n}, expected {n}")
                for row in rows:
                    b = float(row["baseline_recall"])
                    r = float(row["role_aware_recall"])
                    g = float(row["absolute_gain"])
                    lo = float(row["ci_low"])
                    hi = float(row["ci_high"])
                    p = float(row["sign_test_p_holm"])
                    if not all(math.isfinite(x) for x in (b, r, g, lo, hi, p)):
                        errors.append(f"non-finite value in category {row['question_type']}")
                        continue
                    if not (0 <= b <= 1 and 0 <= r <= 1 and 0 <= lo <= hi <= 1 and 0 <= p <= 1):
                        errors.append(f"out-of-range value in category {row['question_type']}")
                    if not close(r - b, g, tol=1e-5):
                        errors.append(f"gain mismatch in category {row['question_type']}")
            except (TypeError, ValueError, KeyError) as exc:
                errors.append(f"could not parse question-type CSV: {exc}")

    provenance = audit.get("provenance", {})
    dataset_hash = provenance.get("dataset_file_sha256")
    hash_status = str(dataset_hash or "").strip().lower()
    if not hash_status or any(
        marker in hash_status
        for marker in ("none", "null", "not present", "not recorded", "missing", "unavailable")
    ):
        warnings.append("dataset SHA-256 is absent; this is an artifact-consistency check, not a full data reproduction")
    if provenance.get("raw_per_question_export_available_in_uploaded_files") is False:
        warnings.append("privacy-safe per-question export is not included; aggregate checks cannot reproduce paired inference")

    if errors:
        print("FAIL: release artifact validation found inconsistencies")
        for item in errors:
            print(f"  - {item}")
        for item in warnings:
            print(f"WARNING: {item}")
        return 1

    print("PASS: committed aggregate artifacts are internally consistent")
    print(f"  held-out questions: {n}")
    print(f"  baseline evidence recall: {baseline:.6f}")
    print(f"  role-aware evidence recall: {role_aware:.6f}")
    print(f"  paired gain: {gain:.6f}")
    print(f"  question-type rows: {len(rows)}")
    for item in warnings:
        print(f"WARNING: {item}")
    print("Scope: consistency validation only; no model retraining or independent replication.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
