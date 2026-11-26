from memweave.comparison import compare_run_metrics, configuration_differences


def _record(run_id, recall, budget=0.1, model="lr"):
    return {
        "run_id": run_id,
        "created_at": f"2026-11-{27 if run_id == 'new' else 26:02d}T00:00:00+00:00",
        "config": {"evaluation": {"budget": budget}, "model": {"kind": model}},
        "summary": {
            "primary_pool": "same_pipeline",
            "n_dev": 100,
            "n_test": 100,
            "main_results": [
                {
                    "pool": "same_pipeline",
                    "method": "LR (tuned)",
                    "recall@budget": recall,
                    "ci_low": recall - 0.02,
                    "ci_high": recall + 0.02,
                    "n_test_questions": 100,
                }
            ],
        },
    }


def test_compare_run_metrics_flattens_registry_summaries():
    records = [_record("old", 0.40), _record("new", 0.45)]

    rows = compare_run_metrics(records)

    assert len(rows) == 2
    assert {row["run_id"] for row in rows} == {"old", "new"}
    assert rows[0]["pool"] == "same_pipeline"
    assert rows[0]["method"] == "LR (tuned)"
    assert rows[0]["primary_pool"] == "same_pipeline"
    assert rows[0]["n_test"] == 100


def test_compare_run_metrics_can_filter_selected_runs():
    records = [_record("old", 0.40), _record("new", 0.45)]

    rows = compare_run_metrics(records, ["new"])

    assert len(rows) == 1
    assert rows[0]["run_id"] == "new"


def test_compare_run_metrics_skips_malformed_summaries():
    records = [
        {"run_id": "empty", "summary": {"main_results": None}},
        {"run_id": "bad-row", "summary": {"main_results": ["not a metric"]}},
    ]

    assert compare_run_metrics(records) == []


def test_configuration_differences_reports_only_changed_nested_paths():
    records = [_record("old", 0.40), _record("new", 0.45, budget=0.2, model="hgb")]

    differences = configuration_differences(records, ["old", "new"])

    assert [item["path"] for item in differences] == [
        "evaluation.budget",
        "model.kind",
    ]
    assert differences[0]["values"] == {"old": 0.1, "new": 0.2}


def test_configuration_differences_requires_two_known_runs():
    records = [_record("old", 0.40)]

    assert configuration_differences(records, ["old", "missing"]) == []



def _provenance(**overrides):
    values = {
        "dataset_sha256": "a" * 64,
        "dev_split_sha256": "b" * 64,
        "test_split_sha256": "c" * 64,
        "metric_protocol": "memweave.session_evidence_recall.v1",
        "budget_fraction": 0.10,
        "budget_unit": "word_count_proxy",
        "primary_pool": "same_pipeline",
    }
    values.update(overrides)
    return values


def test_assess_run_comparability_accepts_matching_provenance():
    from memweave.comparison import assess_run_comparability

    records = [
        {**_record("old", 0.40), "summary": {
            **_record("old", 0.40)["summary"], "provenance": _provenance()
        }},
        {**_record("new", 0.45), "summary": {
            **_record("new", 0.45)["summary"], "provenance": _provenance()
        }},
    ]

    result = assess_run_comparability(records, ["old", "new"])

    assert result["status"] == "directly_comparable"
    assert result["differences"] == {}
    assert result["missing"] == {}
    assert "test_split_sha256" in result["matched_fields"]


def test_assess_run_comparability_rejects_different_dataset_or_split():
    from memweave.comparison import assess_run_comparability

    records = [
        {**_record("old", 0.40), "summary": {
            **_record("old", 0.40)["summary"], "provenance": _provenance()
        }},
        {**_record("new", 0.45), "summary": {
            **_record("new", 0.45)["summary"],
            "provenance": _provenance(test_split_sha256="d" * 64),
        }},
    ]

    result = assess_run_comparability(records, ["old", "new"])

    assert result["status"] == "not_comparable"
    assert result["differences"]["test_split_sha256"] == {
        "old": "c" * 64, "new": "d" * 64
    }


def test_assess_run_comparability_marks_legacy_runs_insufficient():
    from memweave.comparison import assess_run_comparability

    result = assess_run_comparability(
        [_record("old", 0.40), _record("new", 0.45)],
        ["old", "new"],
    )

    assert result["status"] == "insufficient_provenance"
    assert "old" in result["missing"]
    assert "dataset_sha256" in result["missing"]["old"]


def test_assess_run_comparability_requires_two_registered_runs():
    from memweave.comparison import assess_run_comparability

    result = assess_run_comparability([_record("old", 0.40)], ["old", "missing"])

    assert result["status"] == "insufficient_runs"
