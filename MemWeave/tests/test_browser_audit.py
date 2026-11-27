import json

import pytest

from memweave.browser_audit import FORMAT, load_browser_audit, write_browser_audit


def browser_export():
    return {
        "format": FORMAT,
        "schemaVersion": 2,
        "source": "synthetic fixture",
        "question": "Which priority was retained?",
        "annotatedAt": "2026-11-27T00:00:00Z",
        "relevantEvidenceIds": ["a", "c"],
        "candidateEvidence": [
            {"id": "a", "text": "Evidence retention is a priority."},
            {"id": "b", "text": "Python is used in the pipeline."},
            {"id": "c", "text": "Downstream answer quality is evaluated."},
        ],
        "evaluations": [
            {"budgetPercent": 10, "policy": "coverage", "lambda": 0.25,
             "budgetCap": 9, "usedCost": 8, "solver": "Heuristic",
             "selectedIds": ["a", "b"], "retrievalIds": ["a"]},
            {"budgetPercent": 20, "policy": "coverage", "lambda": 0.25,
             "budgetCap": 18, "usedCost": 17, "solver": "Heuristic",
             "selectedIds": ["a", "b", "c"], "retrievalIds": ["c", "a"]},
        ],
    }


def test_browser_audit_recomputes_retention_and_retrieval_separately(tmp_path):
    source = tmp_path / "browser.json"
    source.write_text(json.dumps(browser_export()), encoding="utf-8")
    result = load_browser_audit(source)
    ten, twenty = result["results"]
    assert ten["retention_recall"] == pytest.approx(0.5)
    assert ten["retrieval_precision_at_5"] == pytest.approx(0.2)
    assert ten["retrieval_f1_at_5"] == pytest.approx(2 * 0.2 * 0.5 / 0.7)
    assert ten["retrieval_recall_at_5"] == pytest.approx(0.5)
    assert twenty["retention_recall"] == pytest.approx(1.0)
    assert twenty["retrieval_precision_at_5"] == pytest.approx(0.4)
    assert result["task_type"] == "browser_atomic_evidence_diagnostic"
    assert "LongMemEval" in result["limitations"][0]


def test_browser_audit_rejects_unknown_gold_ids(tmp_path):
    payload = browser_export()
    payload["relevantEvidenceIds"] = ["missing"]
    source = tmp_path / "bad.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="relevantEvidenceIds"):
        load_browser_audit(source)


def test_browser_audit_rejects_duplicate_candidate_ids(tmp_path):
    payload = browser_export()
    payload["candidateEvidence"][1]["id"] = "a"
    source = tmp_path / "bad.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="unique"):
        load_browser_audit(source)


def test_browser_audit_writes_derived_artifacts_without_raw_candidate_text(tmp_path):
    source = tmp_path / "browser.json"
    source.write_text(json.dumps(browser_export()), encoding="utf-8")
    result = load_browser_audit(source)
    output = write_browser_audit(result, tmp_path / "out")
    assert (output / "browser_atomic_audit.json").is_file()
    assert (output / "browser_atomic_audit.csv").is_file()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["input_sha256"] == result["input_sha256"]
    derived = (output / "browser_atomic_audit.json").read_text(encoding="utf-8")
    assert "Evidence retention is a priority." not in derived



def batch_export(question, relevant_ids, rank_retrieval, coverage_retrieval):
    payload = browser_export()
    payload["question"] = question
    payload["relevantEvidenceIds"] = relevant_ids
    payload["evaluations"] = [
        {
            "budgetPercent": 10, "policy": "rank", "lambda": 0.25,
            "budgetCap": 9, "usedCost": 8, "solver": "Heuristic",
            "selectedIds": ["a", "b"], "retrievalIds": rank_retrieval,
        },
        {
            "budgetPercent": 10, "policy": "coverage", "lambda": 0.25,
            "budgetCap": 9, "usedCost": 8, "solver": "Heuristic",
            "selectedIds": ["a", "c"], "retrievalIds": coverage_retrieval,
        },
    ]
    return payload


def test_batch_aggregates_matched_questions_and_paired_policy_deltas(tmp_path):
    from memweave.browser_audit import load_browser_audit_batch, write_browser_audit_batch

    first = tmp_path / "q1.json"
    second = tmp_path / "q2.json"
    first.write_text(json.dumps(batch_export("Which claim A?", ["a"], ["a"], ["c"])), encoding="utf-8")
    second.write_text(json.dumps(batch_export("Which claim C?", ["c"], ["a"], ["c"])), encoding="utf-8")

    result = load_browser_audit_batch([first, second])
    assert result["question_count"] == 2
    coverage = next(row for row in result["results"] if row["policy"] == "coverage")
    rank = next(row for row in result["results"] if row["policy"] == "rank")
    assert coverage["metrics"]["retention_recall"]["mean"] == pytest.approx(1.0)
    assert rank["metrics"]["retention_recall"]["mean"] == pytest.approx(0.5)
    paired = result["paired_deltas_vs_rank"][0]
    assert paired["deltas"]["retrieval_recall_at_5"]["mean"] == pytest.approx(0.0)
    assert paired["deltas"]["retrieval_recall_at_5"]["n_questions"] == 2

    output = write_browser_audit_batch(result, tmp_path / "aggregate")
    assert (output / "browser_atomic_batch.json").is_file()
    assert (output / "browser_atomic_batch.csv").is_file()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["input_sha256"]) == 2
    serialized = (output / "browser_atomic_batch.json").read_text(encoding="utf-8")
    assert "Which claim A?" not in serialized
    assert "Evidence retention is a priority." not in serialized


def test_batch_rejects_different_candidate_sets(tmp_path):
    from memweave.browser_audit import load_browser_audit_batch

    first = batch_export("Question one?", ["a"], ["a"], ["a"])
    second = batch_export("Question two?", ["a"], ["a"], ["a"])
    second["candidateEvidence"][0]["text"] = "Changed evidence text."
    p1, p2 = tmp_path / "one.json", tmp_path / "two.json"
    p1.write_text(json.dumps(first), encoding="utf-8")
    p2.write_text(json.dumps(second), encoding="utf-8")
    with pytest.raises(ValueError, match="same candidate evidence set"):
        load_browser_audit_batch([p1, p2])


def test_batch_rejects_unmatched_retention_selection(tmp_path):
    from memweave.browser_audit import load_browser_audit_batch

    first = batch_export("Question one?", ["a"], ["a"], ["a"])
    second = batch_export("Question two?", ["a"], ["a"], ["a"])
    second["evaluations"][0]["selectedIds"] = ["a"]
    p1, p2 = tmp_path / "one.json", tmp_path / "two.json"
    p1.write_text(json.dumps(first), encoding="utf-8")
    p2.write_text(json.dumps(second), encoding="utf-8")
    with pytest.raises(ValueError, match="not matched"):
        load_browser_audit_batch([p1, p2])
