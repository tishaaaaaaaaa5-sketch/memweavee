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
    assert ten["retrieval_precision_at_5"] == pytest.approx(1.0)
    assert ten["retrieval_recall_at_5"] == pytest.approx(0.5)
    assert twenty["retention_recall"] == pytest.approx(1.0)
    assert twenty["retrieval_precision_at_5"] == pytest.approx(1.0)
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
