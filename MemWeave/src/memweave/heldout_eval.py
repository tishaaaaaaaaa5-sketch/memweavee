"""Leakage-conscious scoring for labelled evidence and frozen-reader outputs."""
from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Iterable, Mapping
from typing import Any

READER_FIELDS = ("reader_id", "reader_version", "prompt_sha256",
                 "decoding_config_sha256", "tokenizer_id")
RECORD_FIELDS = ("question_id", "gold_evidence_ids", "retained_evidence_ids",
                 "retrieved_evidence_ids", "answerable", "gold_answer",
                 "predicted_answer", "abstained")


def measure_token_cost(text: str, encode: Callable[[str], Iterable[int]],
                       tokenizer_id: str) -> dict[str, Any]:
    """Count exact supplied text with the caller's pinned tokenizer encoder."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(tokenizer_id, str) or not tokenizer_id.strip():
        raise ValueError("tokenizer_id must be non-empty")
    ids = list(encode(text))
    if any(not isinstance(item, int) for item in ids):
        raise TypeError("encoder must return integer token IDs")
    return {
        "tokenizer_id": tokenizer_id,
        "token_count": len(ids),
        "utf8_bytes": len(text.encode("utf-8")),
        "character_count": len(text),
        "serialized_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "cost_scope": "exact for supplied serialization and tokenizer only",
    }


def _normalise(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def _f1(prediction: str, reference: str) -> float:
    pred, gold = _normalise(prediction).split(), _normalise(reference).split()
    if not pred or not gold:
        return float(pred == gold)
    remaining: dict[str, int] = {}
    for token in gold:
        remaining[token] = remaining.get(token, 0) + 1
    overlap = 0
    for token in pred:
        if remaining.get(token, 0):
            overlap += 1
            remaining[token] -= 1
    p, r = overlap / len(pred), overlap / len(gold)
    return 2 * p * r / (p + r) if p + r else 0.0


def _set_metrics(selected: list[str], gold: set[str]) -> dict[str, float]:
    hits = len(set(selected) & gold)
    p = hits / len(set(selected)) if selected else 0.0
    r = hits / len(gold)
    return {"precision": p, "recall": r, "f1": 2*p*r/(p+r) if p+r else 0.0}


def evaluate_records(records: Iterable[Mapping[str, Any]],
                     reader: Mapping[str, Any]) -> dict[str, Any]:
    """Score gold evidence, retained/retrieved evidence, and frozen-reader outputs."""
    missing_reader = [key for key in READER_FIELDS if not reader.get(key)]
    if missing_reader:
        raise ValueError("reader metadata missing: " + ", ".join(missing_reader))
    rows = list(records)
    if not rows:
        raise ValueError("at least one record is required")
    seen: set[str] = set()
    output = []
    for index, row in enumerate(rows):
        missing = [key for key in RECORD_FIELDS if key not in row]
        if missing:
            raise ValueError(f"record {index} missing: " + ", ".join(missing))
        qid = row["question_id"]
        if not isinstance(qid, str) or not qid.strip() or qid in seen:
            raise ValueError("question_id must be non-empty and unique")
        seen.add(qid)
        for key in ("gold_evidence_ids", "retained_evidence_ids", "retrieved_evidence_ids"):
            value = row[key]
            if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
                raise ValueError(f"{key} must be a list of non-empty strings")
            if len(value) != len(set(value)):
                raise ValueError(f"{key} contains duplicate IDs")
        gold = set(row["gold_evidence_ids"])
        if not gold:
            raise ValueError("gold_evidence_ids cannot be empty")
        if not isinstance(row["answerable"], bool) or not isinstance(row["abstained"], bool):
            raise ValueError("answerable and abstained must be booleans")
        if not isinstance(row["gold_answer"], str) or not isinstance(row["predicted_answer"], str):
            raise ValueError("gold_answer and predicted_answer must be strings")
        retained = _set_metrics(row["retained_evidence_ids"], gold)
        retrieved = _set_metrics(row["retrieved_evidence_ids"], gold)
        answerable = row["answerable"]
        output.append({
            "question_id": qid,
            "retention_precision": retained["precision"],
            "retention_recall": retained["recall"],
            "retention_f1": retained["f1"],
            "retrieval_precision": retrieved["precision"],
            "retrieval_recall": retrieved["recall"],
            "retrieval_f1": retrieved["f1"],
            "answerable": answerable,
            "answer_exact_match": (
                float(_normalise(row["predicted_answer"]) == _normalise(row["gold_answer"]))
                if answerable else None
            ),
            "answer_token_f1": (
                _f1(row["predicted_answer"], row["gold_answer"]) if answerable else None
            ),
            "abstained": row["abstained"],
            "abstention_correct": row["abstained"] if not answerable else not row["abstained"],
        })

    def avg(key: str, subset: list[dict[str, Any]]) -> float | None:
        values = [float(row[key]) for row in subset if row[key] is not None]
        return sum(values) / len(values) if values else None

    answerable_rows = [row for row in output if row["answerable"]]
    unanswerable_rows = [row for row in output if not row["answerable"]]
    return {
        "format": "memweave-heldout-evaluation-v1",
        "question_count": len(output),
        "answerable_question_count": len(answerable_rows),
        "unanswerable_question_count": len(unanswerable_rows),
        "reader": dict(reader),
        "macro_metrics": {
            "retention_precision": avg("retention_precision", output),
            "retention_recall": avg("retention_recall", output),
            "retention_f1": avg("retention_f1", output),
            "retrieval_precision": avg("retrieval_precision", output),
            "retrieval_recall": avg("retrieval_recall", output),
            "retrieval_f1": avg("retrieval_f1", output),
            "answer_exact_match": avg("answer_exact_match", answerable_rows),
            "answer_token_f1": avg("answer_token_f1", answerable_rows),
            "unanswerable_abstention_accuracy": avg("abstention_correct", unanswerable_rows),
            "answerable_non_abstention_rate": avg("abstention_correct", answerable_rows),
        },
        "per_question": output,
        "limitations": [
            "Gold evidence and answer labels require human quality control.",
            "Reader outputs must use the identical frozen reader, prompt, and decoding configuration.",
            "Token counts cover only the exact supplied serialization and tokenizer.",
            "This scorer does not train or validate the LR selector or MW-ECS.",
            "Use conversation-cluster splits and cluster-level confidence intervals.",
        ],
    }
