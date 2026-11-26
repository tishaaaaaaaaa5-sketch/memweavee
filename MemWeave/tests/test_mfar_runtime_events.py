from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mfar_runtime_event_writer import MFARRuntimeEventWriter
from validate_mfar_runtime_events import ValidationError, load_events, validate

RUN = "run_" + "a" * 20
QUESTION = "q_" + "b" * 20
SOURCE = "src_" + "c" * 32
CANDIDATE = "cand_" + "d" * 32
ANSWER = "ans_" + "e" * 32


def make_ledger(path: Path) -> list[dict]:
    writer = MFARRuntimeEventWriter(path, run_id=RUN, split="test")
    common = {"question_id": QUESTION}
    writer.emit("source_observed", **common, source_session_id=SOURCE, output_ids=[SOURCE])
    writer.emit(
        "candidate_constructed", **common, source_session_id=SOURCE,
        candidate_occurrence_id=CANDIDATE, input_ids=[SOURCE], output_ids=[CANDIDATE],
    )
    writer.emit("candidate_pool_built", **common, input_ids=[CANDIDATE], output_ids=[CANDIDATE])
    writer.emit(
        "qa_evidence_assembled", **common, input_ids=[CANDIDATE], output_ids=[CANDIDATE],
        metadata={"selection_method": "bm25", "top_k": 1},
    )
    writer.emit(
        "answer_generated", **common, input_ids=[CANDIDATE], output_ids=[ANSWER],
        metadata={"selection_method": "bm25", "evaluation_correct": True},
    )
    return load_events(path)


def test_writer_emits_a_valid_opaque_lineage_ledger(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    events = make_ledger(path)
    summary = validate(events)
    assert summary["questions"] == 1
    assert summary["questions_with_answer"] == 1


@pytest.mark.parametrize("field,value", [
    ("question_id", "Who is Alice?"),
    ("source_session_id", "alice@example.com"),
    ("candidate_occurrence_id", "raw candidate text"),
])
def test_writer_rejects_non_opaque_identifiers(tmp_path: Path, field: str, value: str):
    writer = MFARRuntimeEventWriter(tmp_path / "events.jsonl", run_id=RUN)
    kwargs = {"question_id": QUESTION, field: value}
    with pytest.raises(ValueError):
        writer.emit("source_observed", **kwargs)


@pytest.mark.parametrize("metadata", [
    {"stage_note": "contains raw conversation"},
    {"selection_method": "Alice asked about her diagnosis"},
    {"model_id": "private model name"},
    {"config_sha256": "not-a-hash"},
    {"candidate_count": True},
    {"budget": float("nan")},
    {"top_k": [1, 2]},
])
def test_writer_rejects_free_form_or_invalid_metadata(tmp_path: Path, metadata: dict):
    writer = MFARRuntimeEventWriter(tmp_path / "events.jsonl", run_id=RUN)
    with pytest.raises((TypeError, ValueError)):
        writer.emit("source_observed", question_id=QUESTION, metadata=metadata)


def test_writer_rejects_invalid_run_metadata(tmp_path: Path):
    with pytest.raises(ValueError):
        MFARRuntimeEventWriter(tmp_path / "events.jsonl", run_id="personal-run-name")
    with pytest.raises(ValueError):
        MFARRuntimeEventWriter(tmp_path / "events2.jsonl", run_id=RUN, split="Alice's data")


def test_validator_independently_rejects_raw_identifier(tmp_path: Path):
    events = make_ledger(tmp_path / "events.jsonl")
    events[0]["question_id"] = "Alice asked about her family"
    with pytest.raises(ValidationError, match="opaque"):
        validate(events)


def test_validator_independently_rejects_free_form_metadata(tmp_path: Path):
    events = make_ledger(tmp_path / "events.jsonl")
    events[0]["metadata"] = {"stage_note": "raw user text"}
    with pytest.raises(ValidationError, match="unsupported metadata"):
        validate(events)


def test_validator_rejects_mixed_run_ids_and_broken_lineage(tmp_path: Path):
    events = make_ledger(tmp_path / "events.jsonl")
    mixed = [dict(event) for event in events]
    mixed[-1]["run_id"] = "run_" + "f" * 20
    with pytest.raises(ValidationError, match="mixes multiple run_ids"):
        validate(mixed)

    broken = [dict(event) for event in events]
    broken[2]["input_ids"] = ["cand_" + "9" * 32]
    with pytest.raises(ValidationError, match="pool input/output order mismatch"):
        validate(broken)
