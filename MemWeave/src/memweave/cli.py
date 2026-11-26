"""Command-line entry point for MemWeave research runs and artifact checks."""
import argparse
import subprocess
import sys
from pathlib import Path

from memweave import __version__
from memweave.config import load_config


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _evaluate(config_path: str) -> int:
    config = load_config(config_path)
    root = _repo_root()
    results_dir = Path(
        config.get("evaluation", {}).get(
            "results_dir", "MemWeave/results/final_locked_test"
        )
    )
    if not results_dir.is_absolute():
        results_dir = root / results_dir
    validator = root / "MemWeave" / "scripts" / "validate_release.py"
    if not validator.is_file():
        raise FileNotFoundError(f"Release validator not found: {validator}")
    print("Mode: aggregate artifact audit (no model retraining or benchmark rerun).")
    return subprocess.run(
        [sys.executable, str(validator), "--results-dir", str(results_dir)],
        check=False,
    ).returncode


def _run(config_path: str) -> int:
    config = load_config(config_path)
    if config.get("evaluation", {}).get("mode") != "pipeline":
        raise ValueError("memweave run requires evaluation.mode: pipeline")
    from memweave.runner import run_pipeline

    result = run_pipeline(config)
    print(f"Pipeline completed. Artifacts: {result['artifacts']['output_dir']}")
    print(f"Manifest entries: {len(result['artifacts']['manifest']['files'])}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="memweave", description="MemWeave research CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    evaluate = commands.add_parser("evaluate", help="audit committed aggregate experiment results")
    evaluate.add_argument("--config", required=True, help="YAML artifact-audit configuration")
    run = commands.add_parser("run", help="run the extracted pipeline on local benchmark data")
    run.add_argument("--config", required=True, help="YAML pipeline configuration")
    commands.add_parser("validate", help="validate the default aggregate release")
    commands.add_parser("serve", help="launch the optional Streamlit dashboard")
    args = parser.parse_args(argv)
    try:
        if args.command == "evaluate":
            return _evaluate(args.config)
        if args.command == "run":
            return _run(args.config)
        if args.command == "validate":
            return _evaluate(str(_repo_root() / "MemWeave" / "configs" / "role_aware.yaml"))
        if args.command == "serve":
            dashboard = _repo_root() / "MemWeave" / "dashboard" / "app.py"
            return subprocess.run(
                [sys.executable, "-m", "streamlit", "run", str(dashboard)],
                check=False,
            ).returncode
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
