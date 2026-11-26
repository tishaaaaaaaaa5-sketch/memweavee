#!/usr/bin/env python3
"""Audit real Stage B/C MFAR retention traces; never infer unobserved stages.

Input is the JSONL produced by assemble_mfar_retention_traces.py from the
original Stage B/C candidate export. Outputs are aggregate, privacy-minimised
CSV/JSON summaries. No synthetic records or failure labels are generated.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

FAILURE_MODES = ("construction", "compression", "retrieval", "answering")


def stop(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def load_traces(path: Path) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as exc:
                    stop(f"invalid JSON on line {line_no}: {exc}")
                if not isinstance(item, dict):
                    stop(f"line {line_no}: trace must be a JSON object")
                traces.append(item)
    except OSError as exc:
        stop(f"cannot read {path}: {exc}")
    if not traces:
        stop("input JSONL contains no traces")
    return traces


def trace_metrics(trace: dict[str, Any]) -> dict[str, Any]:
    if trace.get("schema_version") != "0.2.0":
        stop(f"unsupported schema version: {trace.get('schema_version')!r}")

    query = trace.get("query") or {}
    query_id = query.get("query_id")
    if not isinstance(query_id, str) or not query_id:
        stop("trace has no query.query_id")
    variant = (trace.get("diagnosis") or {}).get("feature_snapshot", {}).get("variant")
    if not isinstance(variant, str) or not variant:
        stop(f"{query_id}: missing feature_snapshot.variant")

    pipeline = trace.get("pipeline") or {}
    source = pipeline.get("source_evidence") or []
    candidates = pipeline.get("candidate_memory") or []
    stored = pipeline.get("stored_memory") or []
    retrieved = pipeline.get("retrieved_evidence") or []

    evidence_by_id: dict[str, dict[str, Any]] = {}
    for evidence in source:
        eid = evidence.get("evidence_id")
        if not eid or eid in evidence_by_id:
            stop(f"{query_id}/{variant}: missing or duplicate evidence ID")
        evidence_by_id[eid] = evidence

    candidate_by_id: dict[str, dict[str, Any]] = {}
    for memory in candidates:
        mid = memory.get("memory_id")
        if not mid or mid in candidate_by_id:
            stop(f"{query_id}/{variant}: missing or duplicate candidate memory ID")
        refs = memory.get("source_evidence_ids") or []
        if not refs or any(ref not in evidence_by_id for ref in refs):
            stop(f"{query_id}/{variant}: candidate memory has unresolved evidence provenance")
        candidate_by_id[mid] = memory

    gold_evidence_ids = {
        eid for eid, evidence in evidence_by_id.items()
        if evidence.get("relevance_grade") == "gold"
    }
    if not gold_evidence_ids:
        stop(f"{query_id}/{variant}: no gold source evidence")

    retained_candidate_ids: set[str] = set()
    retained_gold_count = 0
    for memory in stored:
        refs = memory.get("source_evidence_ids") or []
        if not refs or any(ref not in evidence_by_id for ref in refs):
            stop(f"{query_id}/{variant}: stored memory has unresolved evidence provenance")
        # The adapter represents a selected candidate as a stored memory item.
        matched = [
            mid for mid, candidate in candidate_by_id.items()
            if candidate.get("source_evidence_ids") == refs
            and candidate.get("content_sha256") == memory.get("content_sha256")
        ]
        if len(matched) != 1:
            stop(f"{query_id}/{variant}: stored item does not map uniquely to a candidate")
        if matched[0] in retained_candidate_ids:
            stop(f"{query_id}/{variant}: candidate appears more than once in stored memory")
        retained_candidate_ids.add(matched[0])
        if any(ref in gold_evidence_ids for ref in refs):
            retained_gold_count += 1

    if retrieved:
        stop(f"{query_id}/{variant}: this adapter's retrieval stage must remain unobserved/empty")

    observability = trace.get("observability") or {}
    required_false = (
        "precompression_trace_available",
        "retrieval_trace_available",
        "answer_trace_available",
    )
    for field in required_false:
        if observability.get(field) is not False:
            stop(f"{query_id}/{variant}: expected {field}=false for this retention-only export")

    diagnosis = trace.get("diagnosis") or {}
    probabilities = diagnosis.get("probabilities") or {}
    oracle = trace.get("oracle_labels") or {}
    for mode in FAILURE_MODES:
        if probabilities.get(mode) is not None:
            stop(f"{query_id}/{variant}: refusing estimated {mode} probability without real lifecycle evidence")
        if oracle.get(mode) is not None:
            stop(f"{query_id}/{variant}: refusing oracle {mode} label for an unobserved lifecycle stage")

    snapshot = diagnosis.get("feature_snapshot") or {}
    retained_cost = snapshot.get("retained_word_cost_proxy")
    budget_cost = snapshot.get("budget_word_cost_proxy")
    budget_utilization = (
        float(retained_cost) / float(budget_cost)
        if retained_cost is not None and budget_cost not in (None, 0)
        else None
    )
    if budget_utilization is not None and not math.isfinite(budget_utilization):
        stop(f"{query_id}/{variant}: invalid budget utilization")

    gold_count = len(gold_evidence_ids)
    stored_count = len(stored)
    return {
        "query_id": query_id,
        "variant": variant,
        "candidate_count": len(candidates),
        "gold_candidate_count": gold_count,
        "stored_count": stored_count,
        "retained_gold_count": retained_gold_count,
        "gold_candidates_not_retained": gold_count - retained_gold_count,
        "retention_recall": retained_gold_count / gold_count if gold_count else None,
        "retention_precision": retained_gold_count / stored_count if stored_count else 0.0,
        "candidate_retention_rate": stored_count / len(candidates) if candidates else 0.0,
        "retained_word_cost_proxy": retained_cost,
        "budget_word_cost_proxy": budget_cost,
        "budget_utilization": budget_utilization,
        "retrieval_observed": False,
        "answering_observed": False,
        "construction_label": "NOT_OBSERVABLE",
        "compression_label": "NOT_OBSERVABLE",
        "retrieval_label": "NOT_OBSERVABLE",
        "answering_label": "NOT_OBSERVABLE",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="real MFAR retention JSONL")
    parser.add_argument("--per-trace-output", type=Path, default=Path("mfar_retention_audit_per_trace.csv"))
    parser.add_argument("--summary-output", type=Path, default=Path("mfar_retention_audit_summary.json"))
    args = parser.parse_args()

    traces = load_traces(args.input)
    rows = [trace_metrics(trace) for trace in traces]

    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    by_query: dict[str, dict[str, tuple[Any, ...]]] = defaultdict(dict)
    for row in rows:
        key = (row["query_id"], row["variant"])
        if key in by_key:
            stop(f"duplicate trace for query/variant: {key}")
        by_key[key] = row
        # Candidate pool signature across conditions: counts plus gold count.
        by_query[row["query_id"]][row["variant"]] = (
            row["candidate_count"], row["gold_candidate_count"]
        )

    variant_sets = {tuple(sorted(v.keys())) for v in by_query.values()}
    if len(variant_sets) != 1:
        stop("questions do not share the same complete set of variants")
    for query_id, variants in by_query.items():
        if len(set(variants.values())) != 1:
            stop(f"{query_id}: candidate pool/gold count differs across variants")

    summary: dict[str, Any] = {
        "input": str(args.input),
        "trace_count": len(rows),
        "question_count": len(by_query),
        "variants": {},
        "interpretation": {
            "measured": "budgeted session-retention selection over the original Stage B/C candidate export",
            "not_measured": [
                "source-to-candidate construction",
                "pre/post-compression fidelity",
                "separate retrieval",
                "answer generation or answer support",
            ],
            "failure_labels": "All four MFAR labels remain NOT_OBSERVABLE; this audit does not train or apply a failure estimator.",
            "warning": "Retention misses are reported as missed gold candidates, not relabelled as construction or compression failures.",
        },
    }

    for variant in sorted(next(iter(variant_sets))):
        group = [row for row in rows if row["variant"] == variant]
        total_gold = sum(row["gold_candidate_count"] for row in group)
        total_retained_gold = sum(row["retained_gold_count"] for row in group)
        total_stored = sum(row["stored_count"] for row in group)
        total_candidates = sum(row["candidate_count"] for row in group)
        recalls = [row["retention_recall"] for row in group]
        precisions = [row["retention_precision"] for row in group]
        utils = [row["budget_utilization"] for row in group if row["budget_utilization"] is not None]
        summary["variants"][variant] = {
            "question_count": len(group),
            "candidate_count_total": total_candidates,
            "gold_candidate_count_total": total_gold,
            "stored_count_total": total_stored,
            "retained_gold_count_total": total_retained_gold,
            "gold_candidates_not_retained_total": total_gold - total_retained_gold,
            "micro_retention_recall": total_retained_gold / total_gold if total_gold else None,
            "macro_retention_recall": mean(recalls) if recalls else None,
            "micro_retention_precision": total_retained_gold / total_stored if total_stored else 0.0,
            "mean_candidate_retention_rate": mean(row["candidate_retention_rate"] for row in group),
            "mean_budget_utilization": mean(utils) if utils else None,
        }

    args.per_trace_output.parent.mkdir(parents=True, exist_ok=True)
    columns = list(rows[0].keys())
    with args.per_trace_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"Audited {len(rows)} real traces across {len(by_query)} questions.")
    print("Candidate-pool consistency and evidence provenance checks passed.")
    print("All four MFAR failure modes remain NOT_OBSERVABLE; no labels were inferred.")
    for variant, metrics in summary["variants"].items():
        print(
            f"{variant}: micro retention recall={metrics['micro_retention_recall']:.6f}, "
            f"gold missed={metrics['gold_candidates_not_retained_total']}, "
            f"mean budget utilization={metrics['mean_budget_utilization']}"
        )
    print(f"Per-trace CSV: {args.per_trace_output.resolve()}")
    print(f"Summary JSON: {args.summary_output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
