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
