import pytest

from memweave.registry import RunRegistry


def test_registry_records_and_retrieves_completed_run(tmp_path):
    registry = RunRegistry(tmp_path / "runs.sqlite3")
    saved = registry.record(
        run_id="run-001",
        output_dir=tmp_path / "output",
        manifest_sha256="a" * 64,
        input_sha256="b" * 64,
        config={"evaluation": {"budget": 0.1}},
        summary={"primary_pool": "same_pipeline", "n_test": 12},
        created_at="2026-01-01T00:00:00+00:00",
    )

    assert saved["run_id"] == "run-001"
    assert saved["status"] == "completed"
    assert saved["config"]["evaluation"]["budget"] == 0.1
    assert saved["summary"]["n_test"] == 12
    assert saved["manifest_sha256"] == "a" * 64


def test_registry_lists_newest_first_and_respects_limit(tmp_path):
    registry = RunRegistry(tmp_path / "runs.sqlite3")
    for run_id, date in [
        ("older", "2026-01-01T00:00:00+00:00"),
        ("newer", "2026-01-02T00:00:00+00:00"),
    ]:
        registry.record(
            run_id=run_id,
            output_dir=tmp_path / run_id,
            manifest_sha256="c" * 64,
            config={},
            summary={},
            created_at=date,
        )

    assert [item["run_id"] for item in registry.list_runs(limit=1)] == ["newer"]


def test_registry_rejects_duplicate_ids_and_invalid_limits(tmp_path):
    registry = RunRegistry(tmp_path / "runs.sqlite3")
    kwargs = {
        "run_id": "same-id",
        "output_dir": tmp_path,
        "manifest_sha256": "d" * 64,
        "config": {},
        "summary": {},
    }
    registry.record(**kwargs)
    with pytest.raises(Exception):
        registry.record(**kwargs)
    with pytest.raises(ValueError):
        registry.list_runs(limit=0)


def test_registry_missing_run_is_explicit(tmp_path):
    registry = RunRegistry(tmp_path / "runs.sqlite3")
    with pytest.raises(KeyError, match="not found"):
        registry.get("missing")
