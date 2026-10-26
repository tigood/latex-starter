from pathlib import Path

import pytest

from latex_starter import cli
from latex_starter.environment import Check, EnvironmentReport


@pytest.fixture(autouse=True)
def no_real_diagnostics(monkeypatch):
    monkeypatch.setattr(cli, "diagnose", lambda *args: EnvironmentReport((Check("mock", "OK", "available", True),)))


def test_help_and_version(capsys):
    for option in ("--help", "--version"):
        with pytest.raises(SystemExit) as error:
            cli.main([option])
        assert error.value.code == 0
    assert "0.1.0" in capsys.readouterr().out


def test_list_and_doctor(capsys):
    assert cli.main(["list"]) == 0
    assert "course-report" in capsys.readouterr().out
    assert cli.main(["doctor"]) == 0


def test_dry_run_is_side_effect_free(tmp_path, monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail("dry run attempted side effect")
    for name in ("write_project", "compile_project", "open_project", "diagnose"):
        monkeypatch.setattr(cli, name, forbidden)
    assert cli.main(["new", "test", "--yes", "--dry-run", "--compile", "--open",
                     "--output-dir", str(tmp_path / "absent-parent")]) == 0
    assert list(tmp_path.iterdir()) == []
    assert "Dry run" in capsys.readouterr().out


def test_parameter_mode(tmp_path):
    assert cli.main(["new", "english", "--yes", "--language", "en", "--structure", "single",
                     "--no-bibliography", "--no-compile", "--no-open", "--output-dir", str(tmp_path)]) == 0
    assert (tmp_path / "english/main.tex").is_file()
    assert not (tmp_path / "english/references").exists()


def test_interactive_wizard(tmp_path, monkeypatch):
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    # Template, language, structure, five features, name, title, author,
    # institution, output, compile, open, final confirmation.
    answers = iter(["notes", "en", "single", "n", "n", "n", "n", "n", "wizard",
                    "Wizard title", "", "", str(tmp_path), "n", "n", "y"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert cli.main(["new"]) == 0
    assert (tmp_path / "wizard/main.tex").is_file()


def test_interactive_cancel_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli, "yes_no", lambda *args: False)
    monkeypatch.setattr(cli, "collect", lambda values, templates: (
        dict(project_name="cancel", output_dir=str(tmp_path)), templates["notes"]))
    assert cli.main(["new"]) == 0
    assert not list(tmp_path.iterdir())


def test_missing_project_and_unknown_template(tmp_path):
    assert cli.main(["new", "--yes", "--output-dir", str(tmp_path)]) == 2
    assert cli.main(["new", "test", "--yes", "--template", "unknown"]) == 2
    assert not list(tmp_path.iterdir())


def test_render_failure_never_creates_target(tmp_path, monkeypatch):
    from jinja2 import UndefinedError
    def fail(*args):
        raise UndefinedError("bad template")
    monkeypatch.setattr(cli, "render", fail)
    assert cli.main(["new", "bad", "--yes", "--output-dir", str(tmp_path)]) == 2
    assert not list(tmp_path.iterdir())


def test_no_open_without_successful_build(tmp_path, monkeypatch):
    def forbidden(*args):
        pytest.fail("Editor should not launch without successful compilation")
    monkeypatch.setattr(cli, "open_project", forbidden)
    assert cli.main(["new", "test", "--yes", "--open", "--no-compile", "--output-dir", str(tmp_path)]) == 0


@pytest.mark.parametrize("success,returncode,expected", [(True, 0, 0), (False, 1, 1), (False, None, 0)])
def test_creation_build_statuses(tmp_path, monkeypatch, success, returncode, expected):
    from latex_starter.compiler import BuildResult
    monkeypatch.setattr(cli, "compile_project", lambda project, bibliography: BuildResult(
        success, "mock build", project / "build/main.pdf", project / "build/main.log", returncode))
    assert cli.main(["new", "test", "--yes", "--compile", "--output-dir", str(tmp_path)]) == expected
    assert (tmp_path / "test/main.tex").is_file()
