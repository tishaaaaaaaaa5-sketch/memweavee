"""Configuration loading and validation."""
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path).expanduser().resolve()
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    if not isinstance(config, dict):
        raise ValueError("Configuration root must be a YAML mapping")
    evaluation = config.get("evaluation", {})
    if not isinstance(evaluation, dict):
        raise ValueError("'evaluation' must be a mapping")
    mode = evaluation.get("mode", "artifact_audit")
    if mode not in {"artifact_audit", "pipeline"}:
        raise ValueError(
            f"Unsupported evaluation mode {mode!r}; expected 'artifact_audit' or 'pipeline'."
        )
    if mode == "pipeline":
        pipeline = config.get("pipeline", {})
        if not isinstance(pipeline, dict):
            raise ValueError("'pipeline' must be a mapping")
        if not pipeline.get("longmemeval_path"):
            raise ValueError("pipeline.longmemeval_path is required for pipeline mode")
    return config
