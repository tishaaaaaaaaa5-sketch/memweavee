from memweave.heldout_eval import evaluate_records, measure_token_cost

READER = {
    "reader_id": "fixture",
    "reader_version": "1",
    "prompt_sha256": "prompt",
    "decoding_config_sha256": "decode",
    "tokenizer_id": "fixture-tokenizer",
}


def test_tokenizer_injected_cost():
    result = measure_token_cost("a b", lambda text: text.split(), "fixture")
    assert result["token_count"] == 2
    assert result["utf8_bytes"] == 3
    assert len(result["serialized_text_sha256"]) == 64


def test_separates_retention_retrieval_and_answer_metrics():
    records = [
        {"question_id": "q1", "gold_evidence_ids": ["e1", "e2"],
         "retained_evidence_ids": ["e1"], "retrieved_evidence_ids": ["e1", "e2"],
         "answerable": True, "gold_answer": "Paris", "predicted_answer": "Paris",
         "abstained": False},
        {"question_id": "q2", "gold_evidence_ids": ["e3"],
         "retained_evidence_ids": ["e3"], "retrieved_evidence_ids": [],
         "answerable": False, "gold_answer": "", "predicted_answer": "",
         "abstained": True},
    ]
    result = evaluate_records(records, READER)
    metrics = result["macro_metrics"]
    assert metrics["retention_recall"] == 0.75
    assert metrics["retrieval_recall"] == 0.5
    assert metrics["answer_exact_match"] == 1.0
    assert metrics["unanswerable_abstention_accuracy"] == 1.0


def test_rejects_missing_reader_provenance():
    try:
        evaluate_records([], {"reader_id": "fixture"})
    except ValueError as exc:
        assert "reader_version" in str(exc)
    else:
        raise AssertionError("expected missing reader metadata error")


def test_rejects_duplicate_question_ids():
    row = {"question_id": "q", "gold_evidence_ids": ["e"],
           "retained_evidence_ids": ["e"], "retrieved_evidence_ids": ["e"],
           "answerable": True, "gold_answer": "x", "predicted_answer": "x",
           "abstained": False}
    try:
        evaluate_records([row, dict(row)], READER)
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("expected duplicate question ID error")
