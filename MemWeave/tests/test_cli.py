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
