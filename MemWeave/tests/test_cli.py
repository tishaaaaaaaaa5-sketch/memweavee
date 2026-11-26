from memweave.cli import main



def test_cli_requires_subcommand():
    try:
        main([])
    except SystemExit as exc:
        assert exc.code == 2


def test_cli_version(capsys):
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "0.1.0" in capsys.readouterr().out

def test_run_command_rejects_missing_local_dataset(tmp_path, capsys):
    config = tmp_path / "pipeline.yaml"
    config.write_text(
        "pipeline:\n  longmemeval_path: ./missing.json\nevaluation:\n  mode: pipeline\n",
        encoding="utf-8",
    )
    assert main(["run", "--config", str(config)]) == 2
    assert "local LongMemEval JSON" in capsys.readouterr().err



def test_runs_list_and_show_commands(tmp_path, capsys):
    from memweave.registry import RunRegistry

    db = tmp_path / "runs.sqlite3"
    RunRegistry(db).record(
        run_id="cli-run-1",
        output_dir=tmp_path / "artifacts",
        manifest_sha256="e" * 64,
        config={"evaluation": {"budget": 0.1}},
        summary={"primary_pool": "same_pipeline", "n_test": 5},
    )

    assert main(["runs", "--registry", str(db), "list"]) == 0
    assert "cli-run-1" in capsys.readouterr().out

    assert main(["runs", "--registry", str(db), "show", "cli-run-1"]) == 0
    shown = capsys.readouterr().out
    assert '"manifest_sha256"' in shown
    assert '"n_test": 5' in shown



def test_default_registry_path_finds_memweave_working_directory_location(
    monkeypatch, tmp_path
):
    from memweave import cli

    registry = tmp_path / "MemWeave" / "results" / "run_registry.sqlite3"
    registry.parent.mkdir(parents=True)
    registry.touch()
    monkeypatch.setattr(cli, "_repo_root", lambda: tmp_path)

    assert cli._default_registry_path() == registry

