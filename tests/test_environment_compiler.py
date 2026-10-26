from pathlib import Path
import subprocess

import pytest

from latex_starter import compiler, environment


@pytest.mark.parametrize("missing", ["xelatex", "latexmk", "biber"])
def test_missing_required_dependency(monkeypatch, missing):
    monkeypatch.setattr(environment.shutil, "which", lambda name: None if name == missing else "/bin/" + name)
    monkeypatch.setattr(environment, "_output", lambda args: "1.0")
    report = environment.diagnose("en", True)
    assert not report.ready
    assert any(c.name == missing and c.status == "MISSING" for c in report.checks)


def test_english_ignores_fonts_and_biber(monkeypatch):
    monkeypatch.setattr(environment.shutil, "which", lambda name: None if name in {"fc-match", "biber", "code", "git"} else "/bin/" + name)
    monkeypatch.setattr(environment, "_output", lambda args: "1.0")
    report = environment.diagnose("en", False)
    assert report.ready
    assert not any(c.name == "CJK fonts" for c in report.checks)


def test_font_match_must_be_exact(monkeypatch):
    monkeypatch.setattr(environment.shutil, "which", lambda name: "/bin/fc-match" if name == "fc-match" else None)
    monkeypatch.setattr(environment, "_output", lambda args: "DejaVu Sans")
    assert environment.font_check().status == "MISSING"


def test_font_unverifiable_is_warning(monkeypatch):
    monkeypatch.setattr(environment.shutil, "which", lambda name: None)
    check = environment.font_check()
    assert check.status == "WARN"
    assert "unknown" in check.detail


def test_fandol_fallback(monkeypatch):
    monkeypatch.setattr(environment.shutil, "which", lambda name: "/bin/kpsewhich" if name == "kpsewhich" else None)
    monkeypatch.setattr(environment, "_output", lambda args: "/tex/fonts/" + args[-1])
    assert environment.font_check().status == "OK"


@pytest.mark.parametrize("returncode,pdf,success", [(0, True, True), (1, True, False), (0, False, False)])
def test_build_result(tmp_path, monkeypatch, returncode, pdf, success):
    monkeypatch.setattr(compiler.shutil, "which", lambda name: "/bin/" + name)
    (tmp_path / "main.tex").write_text("source")
    def run(args, **kwargs):
        assert args == compiler.build_command()
        assert kwargs["cwd"] == tmp_path
        assert "shell" not in kwargs
        if pdf:
            (tmp_path / "build/main.pdf").write_bytes(b"pdf")
        return subprocess.CompletedProcess(args, returncode, "build stdout", "! mock error" if returncode else "")
    monkeypatch.setattr(compiler.subprocess, "run", run)
    result = compiler.compile_project(tmp_path)
    assert result.success is success
    assert result.log.read_text().startswith("build stdout")
    assert (tmp_path / "main.tex").read_text() == "source"


def test_missing_build_dependency_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(compiler.shutil, "which", lambda name: None)
    result = compiler.compile_project(tmp_path, True)
    assert not result.success and result.returncode is None
    assert not list(tmp_path.iterdir())


def test_timeout_preserves_output(tmp_path, monkeypatch):
    monkeypatch.setattr(compiler.shutil, "which", lambda name: "/bin/" + name)
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1, output=b"partial output")
    monkeypatch.setattr(compiler.subprocess, "run", timeout)
    result = compiler.compile_project(tmp_path)
    assert not result.success
    assert "partial output" in result.log.read_text()


def test_open_missing_code(tmp_path, monkeypatch):
    monkeypatch.setattr(compiler.shutil, "which", lambda name: None)
    assert not compiler.open_project(tmp_path)[0]
