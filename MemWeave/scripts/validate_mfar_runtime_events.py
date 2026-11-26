#!/usr/bin/env python3
"""Validate lineage and privacy boundaries in a real MFAR runtime JSONL ledger.

This validator consumes only the event file emitted by the instrumented
MemWeave notebook. It does not create data or infer failure labels.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

EVENT_TYPES = {
    "source_observed",
    "candidate_constructed",
    "candidate_pool_built",
    "retention_selected",
    "ranking_metric_computed",
    "qa_evidence_assembled",
    "answer_generated",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_TEXT_KEYS = {
    "text", "content", "query", "prompt", "answer", "source_text",
    "retrieved_text", "conversation", "messages",
}


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_events(path: Path) -> list[dict[str, Any]]:
    events = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValidationError(f"line {line_no}: invalid JSON: {exc}") from exc
                require(isinstance(event, dict), f"line {line_no}: event must be an object")
                events.append(event)
    except OSError as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc
    require(bool(events), "event file contains no records")
    return events


def validate(events: list[dict[str, Any]]) -> dict[str, Any]:
    required = {
        "event_schema_version", "run_id", "event_id", "event_type",
        "occurred_at", "question_id", "source_session_id",
        "candidate_occurrence_id", "input_ids", "output_ids",
        "content_sha256", "metadata", "run_metadata",
    }
    event_ids: set[str] = set()
    run_ids: set[str] = set()
    by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    counts = Counter()

    for index, event in enumerate(events, start=1):
        missing = required - set(event)
        require(not missing, f"event {index}: missing fields {sorted(missing)}")
        require(event["event_schema_version"] == "0.1.0", f"event {index}: unsupported schema version")
        require(event["event_type"] in EVENT_TYPES, f"event {index}: unknown event type")
        require(isinstance(event["run_id"], str) and event["run_id"], f"event {index}: empty run_id")
        require(isinstance(event["event_id"], str) and event["event_id"], f"event {index}: empty event_id")
        require(event["event_id"] not in event_ids, f"event {index}: duplicate event_id")
        event_ids.add(event["event_id"])
        run_ids.add(event["run_id"])
        require(isinstance(event["question_id"], str) and event["question_id"], f"event {index}: missing opaque question_id")
        require(isinstance(event["input_ids"], list) and all(isinstance(x, str) and x for x in event["input_ids"]),
                f"event {index}: input_ids must be a list of non-empty strings")
        require(isinstance(event["output_ids"], list) and all(isinstance(x, str) and x for x in event["output_ids"]),
                f"event {index}: output_ids must be a list of non-empty strings")
        require(len(event["input_ids"]) == len(set(event["input_ids"])), f"event {index}: duplicate input IDs")
        require(len(event["output_ids"]) == len(set(event["output_ids"])), f"event {index}: duplicate output IDs")
        digest = event["content_sha256"]
        require(digest is None or (isinstance(digest, str) and SHA256.fullmatch(digest) is not None),
                f"event {index}: invalid content_sha256")
        try:
            datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValidationError(f"event {index}: invalid occurred_at timestamp") from exc
        require(isinstance(event["metadata"], dict), f"event {index}: metadata must be an object")
        require(isinstance(event["run_metadata"], dict), f"event {index}: run_metadata must be an object")
        forbidden = FORBIDDEN_TEXT_KEYS.intersection(event)
        require(not forbidden, f"event {index}: raw-text fields are forbidden: {sorted(forbidden)}")
        forbidden_meta = FORBIDDEN_TEXT_KEYS.intersection(event["metadata"])
        require(not forbidden_meta, f"event {index}: raw-text metadata fields are forbidden: {sorted(forbidden_meta)}")
        by_question[event["question_id"]].append(event)
        counts[event["event_type"]] += 1

    require(len(run_ids) == 1, f"event file mixes multiple run_ids: {sorted(run_ids)}")

    totals = {
        "source_ids": set(),
        "candidate_ids": set(),
        "answer_ids": set(),
    }
    question_summaries = {}

    for qid, rows in by_question.items():
        source_ids: set[str] = set()
        candidate_ids: set[str] = set()
        candidate_source: dict[str, str] = {}
        pools = []
        retention_events = []
        qa_events = []
        answer_events = []

        for event in rows:
            typ = event["event_type"]
            ins, outs = event["input_ids"], event["output_ids"]
            if typ == "source_observed":
                require(len(outs) == 1, f"{qid}: source_observed must output exactly one source ID")
                require(event["source_session_id"] == outs[0], f"{qid}: source ID field/output mismatch")
                source_ids.add(outs[0])
            elif typ == "candidate_constructed":
                require(len(ins) == 1 and len(outs) == 1, f"{qid}: candidate_constructed needs one source and one candidate")
                require(event["source_session_id"] == ins[0], f"{qid}: candidate source ID/input mismatch")
                require(event["candidate_occurrence_id"] == outs[0], f"{qid}: candidate occurrence ID/output mismatch")
                candidate_ids.add(outs[0])
                candidate_source[outs[0]] = ins[0]
            elif typ == "candidate_pool_built":
                pools.append(event)
            elif typ == "retention_selected":
                retention_events.append(event)
            elif typ == "qa_evidence_assembled":
                qa_events.append(event)
            elif typ == "answer_generated":
                answer_events.append(event)

        require(candidate_ids, f"{qid}: no candidate construction events")
        require(set(candidate_source.values()).issubset(source_ids),
                f"{qid}: candidate references source evidence not observed in this question")
        require(len(pools) == 1, f"{qid}: expected exactly one candidate_pool_built event, found {len(pools)}")
        pool = pools[0]
        pool_ids = pool["output_ids"]
        require(pool["input_ids"] == pool_ids, f"{qid}: candidate pool input/output order mismatch")
        require(len(pool_ids) == len(candidate_ids) and set(pool_ids) == candidate_ids,
                f"{qid}: candidate pool does not match constructed candidate occurrences")

        for event in retention_events:
            require(event["input_ids"] == pool_ids, f"{qid}: retention candidate pool differs from built pool")
            require(set(event["output_ids"]).issubset(set(pool_ids)),
                    f"{qid}: retention output references an unknown candidate")
        require(len(retention_events) <= 1, f"{qid}: multiple primary retention events for one question")

        for event in qa_events:
            require(set(event["input_ids"]).issubset(set(pool_ids)),
                    f"{qid}: QA context input references unknown candidate")
            require(set(event["output_ids"]).issubset(set(event["input_ids"])),
                    f"{qid}: QA context output is not a subset of supplied retained candidates")
            require(len(event["output_ids"]) <= int(event["metadata"].get("top_k", len(event["output_ids"]))),
                    f"{qid}: QA context output exceeds top_k")

        for event in answer_events:
            require(len(event["output_ids"]) == 1, f"{qid}: answer_generated must output one answer ID")
            require(set(event["input_ids"]).issubset(set(pool_ids)),
                    f"{qid}: answer input references unknown candidate")
            method = event["metadata"].get("selection_method")
            matches = [
                qa for qa in qa_events
                if qa["metadata"].get("selection_method") == method
                and qa["output_ids"] == event["input_ids"]
            ]
            require(bool(matches), f"{qid}: answer evidence does not match a recorded QA context")
            totals["answer_ids"].add(event["output_ids"][0])

        totals["source_ids"].update(source_ids)
        totals["candidate_ids"].update(candidate_ids)
        question_summaries[qid] = {
            "source_sessions": len(source_ids),
            "candidate_occurrences": len(candidate_ids),
            "retention_events": len(retention_events),
            "qa_context_events": len(qa_events),
            "answer_events": len(answer_events),
        }

    return {
        "run_id": next(iter(run_ids)),
        "events": len(events),
        "questions": len(by_question),
        "event_counts": dict(counts),
        "unique_source_ids": len(totals["source_ids"]),
        "unique_candidate_ids": len(totals["candidate_ids"]),
        "unique_answer_ids": len(totals["answer_ids"]),
        "questions_with_retention": sum(x["retention_events"] > 0 for x in question_summaries.values()),
        "questions_with_qa_context": sum(x["qa_context_events"] > 0 for x in question_summaries.values()),
        "questions_with_answer": sum(x["answer_events"] > 0 for x in question_summaries.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="run-specific MFAR runtime JSONL file")
    parser.add_argument("--summary-output", type=Path, help="optional path for a JSON validation summary")
    args = parser.parse_args()
    try:
        summary = validate(load_events(args.input))
    except ValidationError as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(summary, indent=2)
    print("MFAR runtime event lineage validation passed.")
    print(rendered)
    if args.summary_output:
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        args.summary_output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Summary written to {args.summary_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
