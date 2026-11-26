from pathlib import Path

import pytest

from memweave.config import load_config


def test_load_role_aware_config():
    path = Path(__file__).parents[1] / "configs" / "role_aware.yaml"
    assert load_config(path)["evaluation"]["mode"] == "artifact_audit"


def test_pipeline_mode_requires_local_input_path(tmp_path):
    path = tmp_path / "pipeline.yaml"
    path.write_text(
        "pipeline:\n  longmemeval_path: ./local.json\nevaluation:\n  mode: pipeline\n",
        encoding="utf-8",
    )
    assert load_config(path)["evaluation"]["mode"] == "pipeline"


def test_pipeline_mode_requires_input_path(tmp_path):
    path = tmp_path / "bad_pipeline.yaml"
    path.write_text("evaluation:\n  mode: pipeline\n", encoding="utf-8")
    with pytest.raises(ValueError, match="longmemeval_path"):
        load_config(path)


def test_rejects_unknown_mode(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("evaluation:\n  mode: train_everything\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported evaluation mode"):
        load_config(path)
