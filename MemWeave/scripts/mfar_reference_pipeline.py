#!/usr/bin/env python3
"""Synthetic, backend-independent MFAR reference pipeline.

This is an instrumentation fixture, not a production memory system. It uses
synthetic evidence and hashes only; failure scenarios are controlled by the
caller. Oracle failure labels remain null and must be independently annotated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCENARIOS = {
    "clean",
    "construction_loss",
    "compression_loss",
    "retrieval_loss",
    "answering_failure",
}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def timestamp_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_scenario(scenario: str, created_at: str | None = None) -> dict[str, Any]:
    """Create one schema-shaped trace for a deterministic synthetic scenario."""
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario must be one of: {', '.join(sorted(SCENARIOS))}")
    now = created_at or timestamp_now()

    # Text exists only in this local synthetic fixture. The trace stores hashes.
    fact = "The synthetic project meeting is scheduled for Tuesday at 10:00."
    answer = "The synthetic project meeting is scheduled for Tuesday at 10:00."
    source_id = "src_synthetic_001"
    evidence_id = "ev_source_001"
    candidate_id = "mem_candidate_001"
    stored_id = "mem_stored_001"
    retrieved_id = "ev_retrieved_001"

    source = [{
        "evidence_id": evidence_id,
        "source_id": source_id,
        "content_sha256": sha256(fact),
        "source_span": None,
        "relevance_grade": "gold",
    }]

    # Construction: evidence may fail to enter the candidate memory.
    candidate = []
    if scenario != "construction_loss":
        candidate.append({
            "memory_id": candidate_id,
            "content_sha256": sha256(fact),
            "source_evidence_ids": [evidence_id],
            "created_at": now,
            "valid_from": None,
            "valid_until": None,
            "supersedes_memory_ids": [],
            "confidence": None,
        })

    # Compression: candidate information may be lost before persistent storage.
    stored = []
    if candidate and scenario != "compression_loss":
        stored.append({
            "memory_id": stored_id,
            "content_sha256": sha256(fact),
            "source_evidence_ids": [evidence_id],
            "created_at": now,
            "valid_from": None,
            "valid_until": None,
            "supersedes_memory_ids": [],
            "confidence": None,
        })

    # Retrieval: stored memory may fail to be returned for this query.
    retrieved = []
    if stored and scenario not in {"retrieval_loss"}:
        retrieved.append({
            "evidence_id": retrieved_id,
            "source_id": stored_id,
            "content_sha256": sha256(fact),
            "source_span": None,
            "relevance_grade": "gold",
        })

    transformations = []
    if source:
        transformations.append({
            "transformation_id": "tr_construction_001",
            "kind": "extract",
            "input_ids": [evidence_id],
            "output_ids": [candidate_id] if candidate else [],
            "timestamp": now,
            "implementation_version": "mfar-reference-0.1.0",
            "metadata": {"stage": "construction", "synthetic_scenario": scenario},
        })
    if candidate:
        transformations.append({
            "transformation_id": "tr_compression_001",
            "kind": "compress",
            "input_ids": [candidate_id],
            "output_ids": [stored_id] if stored else [],
            "timestamp": now,
            "implementation_version": "mfar-reference-0.1.0",
            "metadata": {"stage": "compression", "synthetic_scenario": scenario},
        })

    # Answering failure is represented only when retrieval supplied evidence.
    answer_text = "The meeting is on Friday at 16:00." if scenario == "answering_failure" else answer
    answer_present = bool(retrieved)
    claim_support = []
    if answer_present:
        claim_support.append({
            "claim_id": "claim_synthetic_001",
            "support_status": "unsupported" if scenario == "answering_failure" else "supported",
            "evidence_ids": [] if scenario == "answering_failure" else [retrieved_id],
        })

    return {
        "schema_version": "0.2.0",
        "run_id": "run_synthetic_mfar_001",
        "example_id": "ex_synthetic_" + scenario,
        "created_at": now,
        "dataset": {
            "name": "synthetic_mfar_fixture",
            "revision": "1",
            "checksum_sha256": None,
            "split": "dev",
            "conversation_cluster_id": None,
        },
        "query": {
            "query_id": "q_synthetic_001",
            "content_sha256": sha256("When is the synthetic project meeting?"),
            "question_type": "temporal_fact",
            "requirements": [{"requirement_id": "req_synthetic_001", "kind": "time", "target_hash": None}],
        },
        "observability": {
            "source_archive_available": True,
            "precompression_trace_available": True,
            "memory_provenance_available": True,
            "retrieval_trace_available": True,
            "answer_trace_available": True,
            "unavailable_reasons": [],
        },
        "pipeline": {
            "source_evidence": source,
            "candidate_memory": candidate,
            "stored_memory": stored,
            "retrieved_evidence": retrieved,
            "transformations": transformations,
        },
        "diagnosis": {
            "mode": "multi_label",
            "probabilities": {"construction": None, "compression": None, "retrieval": None, "answering": None},
            "uncertainty": None,
            "model_version": "not_estimated",
            "feature_snapshot": {"synthetic_scenario": scenario},
        },
        # Deliberately null: controlled scenario names are not human oracle labels.
        "oracle_labels": None,
        "controller": {
            "selected_action": "diagnostic_only",
            "policy_version": "reference-no-controller-0.1.0",
            "reason_codes": ["synthetic_instrumentation_fixture"],
            "estimated_quality_gain": None,
            "estimated_incremental_cost": None,
            "estimated_risk": None,
        },
        "outcome": {
            "answer_id": "answer_synthetic_001" if answer_present else None,
            "answer_content_sha256": sha256(answer_text) if answer_present else None,
            "evidence_ids": [retrieved_id] if retrieved else [],
            "status": "answered" if answer_present else "not_evaluated",
            "claim_support": claim_support,
        },
        "cost": {
            "stored_tokens": None,
            "retrieved_tokens": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "latency_ms": None,
            "model_calls": None,
            "estimated_cost_usd": None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="clean")
    parser.add_argument("--output", type=Path, default=Path("mfar_synthetic_trace.json"))
    parser.add_argument("--created-at", default=None, help="Optional ISO-8601 timestamp for reproducibility.")
    args = parser.parse_args()
    trace = run_scenario(args.scenario, args.created_at)
    args.output.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.scenario} synthetic trace: {args.output}")
    print("Oracle labels: null (no human annotation has been performed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
