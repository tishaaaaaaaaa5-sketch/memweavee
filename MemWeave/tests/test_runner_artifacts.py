import json

import pandas as pd

from memweave.runner import write_artifacts


def test_artifact_writer_emits_hash_manifest_and_findings(tmp_path):
    result = write_artifacts(
        tmp_path,
        {"main_results": pd.DataFrame([{"recall": 0.5}])},
        {
            "settings": {"primary_pool": "same_pipeline"},
            "split": {"n_dev": 8, "n_test": 4},
        },
    )
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert "main_results.csv" in manifest["files"]
    assert len(manifest["files"]["main_results.csv"]["sha256"]) == 64
    assert (tmp_path / "findings.txt").is_file()
    assert result["manifest"]["manifest_version"] == 1
