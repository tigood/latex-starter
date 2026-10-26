"""Opt-in clean wheel/pipx/frozen tests; no network or user-global changes.

Set LATEX_STARTER_DISTRIBUTION=1 and LATEX_STARTER_WHEELHOUSE to a directory
containing pip, setuptools, Jinja2 and MarkupSafe wheels. Optional:
LATEX_STARTER_EXECUTABLE for an already built native executable, and
LATEX_STARTER_INTEGRATION=1 for real builds from each installed application.
"""
from dataclasses import dataclass
from email.parser import Parser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv
import zipfile

import pytest

from latex_starter.catalog import TEMPLATE_ROOT

ROOT = Path(__file__).resolve().parents[1]
pytestmark = [pytest.mark.distribution, pytest.mark.skipif(
    os.environ.get("LATEX_STARTER_DISTRIBUTION") != "1",
    reason="Opt in with LATEX_STARTER_DISTRIBUTION=1 and an offline wheelhouse")]


@dataclass
class InstalledApp:
    command: Path
    env: dict[str, str]


def run(command, cwd, env, *, allowed=(0,), timeout=180):
    result = subprocess.run([str(arg) for arg in command], cwd=cwd, env=env,
                            capture_output=True, text=True, errors="replace", timeout=timeout)
    assert result.returncode in allowed, result.stdout + result.stderr
    return result


@pytest.fixture(scope="session")
def offline_env(tmp_path_factory):
    wheelhouse = os.environ.get("LATEX_STARTER_WHEELHOUSE")
    if not wheelhouse or not Path(wheelhouse).is_dir():
        pytest.fail("Distribution tests require LATEX_STARTER_WHEELHOUSE; no network fallback")
    isolated = tmp_path_factory.mktemp("distribution-state")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    env.update(PIP_NO_INDEX="1", PIP_FIND_LINKS=str(Path(wheelhouse).resolve()),
               PIP_NO_CACHE_DIR="1", PIP_DISABLE_PIP_VERSION_CHECK="1",
               PYTHONNOUSERSITE="1", XDG_CACHE_HOME=str(isolated / "cache"),
               XDG_STATE_HOME=str(isolated / "state"), XDG_DATA_HOME=str(isolated / "data"),
               PIPX_DEFAULT_BACKEND="pip")
    return env


@pytest.fixture(scope="session")
def wheel(tmp_path_factory, offline_env):
    output = tmp_path_factory.mktemp("wheel-build")
    run([sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", output, ROOT],
        output, offline_env)
    artifacts = list(output.glob("*.whl"))
    assert len(artifacts) == 1
    return artifacts[0]


@pytest.fixture(scope="session")
def wheel_app(tmp_path_factory, offline_env, wheel):
    root = tmp_path_factory.mktemp("wheel-clean-env")
    venv.EnvBuilder(with_pip=True).create(root / "venv")
    bindir = root / "venv" / ("Scripts" if os.name == "nt" else "bin")
    python = bindir / ("python.exe" if os.name == "nt" else "python")
    run([python, "-m", "pip", "install", wheel], root, offline_env)
    # Assert this is a wheel install without access to the developer checkout.
    check = run([python, "-c", "import latex_starter; print(latex_starter.__file__)"], root, offline_env)
    assert str(root / "venv") in check.stdout
    assert str(ROOT) not in check.stdout
    check = run([python, "-c", "import importlib.util; assert importlib.util.find_spec('PyInstaller') is None"], root, offline_env)
    env = {**offline_env, "PATH": str(bindir) + os.pathsep + offline_env["PATH"]}
    return InstalledApp(bindir / ("latex-starter.exe" if os.name == "nt" else "latex-starter"), env)


@pytest.fixture(scope="session")
def pipx_app(tmp_path_factory, offline_env):
    pytest.importorskip("pipx", reason="Install .[distribution] first")
    root = tmp_path_factory.mktemp("pipx-clean-env")
    bindir = root / "bin"
    env = {**offline_env, "PIPX_HOME": str(root / "home"), "PIPX_BIN_DIR": str(bindir),
           "PIPX_MAN_DIR": str(root / "man"), "PATH": str(bindir) + os.pathsep + offline_env["PATH"]}
    run([sys.executable, "-m", "pipx", "install", "--editable", ROOT, "--python", sys.executable], root, env)
    command = bindir / ("latex-starter.exe" if os.name == "nt" else "latex-starter")
    assert command.is_file()
    return InstalledApp(command, env)


@pytest.fixture(scope="session")
def standalone_app(offline_env):
    value = os.environ.get("LATEX_STARTER_EXECUTABLE")
    if not value:
        pytest.skip("Set LATEX_STARTER_EXECUTABLE to test a previously built native executable")
    command = Path(value).resolve()
    assert command.is_file(), command
    return InstalledApp(command, {**offline_env, "PATH": str(command.parent) + os.pathsep + offline_env["PATH"]})


@pytest.fixture(params=["wheel_app", "pipx_app", "standalone_app"])
def app(request):
    return request.getfixturevalue(request.param)


def test_wheel_inventory_and_metadata(wheel):
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        expected = {"latex_starter/templates/" + p.relative_to(TEMPLATE_ROOT).as_posix()
                    for p in TEMPLATE_ROOT.rglob("*") if p.is_file()}
        assert expected <= names
        assert not any("__pycache__" in name or ".venv" in name for name in names)
        metadata = Parser().parsestr(archive.read(next(n for n in names if n.endswith(".dist-info/METADATA"))).decode())
        assert metadata["Name"] == "latex-starter"
        assert metadata["Requires-Python"] == ">=3.10"
        assert metadata["License-Expression"] == "MIT"
        assert metadata["License-File"] == "LICENSE"
        dependencies = metadata.get_all("Requires-Dist")
        assert all("extra ==" in item for item in dependencies if "jinja2" not in item.lower())
        entrypoints = archive.read(next(n for n in names if n.endswith(".dist-info/entry_points.txt"))).decode()
        assert "latex-starter = latex_starter.cli:main" in entrypoints


@pytest.mark.parametrize("args", [["--help"], ["--version"], ["list"], ["doctor"]])
def test_installed_commands_by_name(app, tmp_path, args):
    assert shutil.which("latex-starter", path=app.env["PATH"]) == str(app.command)
    result = run(["latex-starter", *args], tmp_path, app.env,
                 allowed=(0, 1) if args == ["doctor"] else (0,))
    if args == ["--version"]:
        assert "0.1.0" in result.stdout
    elif args == ["list"]:
        assert all(name in result.stdout for name in ("academic-article", "course-report", "notes"))
    elif args == ["doctor"]:
        assert "xelatex" in result.stdout and "Environment:" in result.stdout


@pytest.mark.parametrize("template", ["academic-article", "course-report", "notes"])
def test_installed_template_options(app, tmp_path, template):
    enabled = template != "notes"
    args = ["latex-starter", "new", "sample", "--yes", "--template", template,
            "--language", "mixed" if enabled else "en", "--structure", "split" if enabled else "single",
            "--no-compile", "--no-open", "--title", "Text & % # _ { }", "--output-dir", str(tmp_path)]
    for flag in ("bibliography", "figures-tables-examples", "code-listing-example", "table-of-contents", "appendix"):
        args.append("--" + ("" if enabled else "no-") + flag)
    run(args, tmp_path, app.env)
    target = tmp_path / "sample"
    source = "\n".join(p.read_text() for p in target.rglob("*.tex"))
    assert r"Text \& \% \# \_ \{ \}" in source
    for marker in ("\\autocite", "\\begin{figure}", "\\begin{lstlisting}", "\\tableofcontents", "\\appendix"):
        assert (marker in source) is enabled
    assert (target / "references/references.bib").is_file() is enabled
    assert (target / "sections").is_dir() is enabled
    assert not (target / "build").exists()


@pytest.mark.parametrize("language,bibliography", [("zh", True), ("en", False)])
def test_installed_real_compile(app, tmp_path, language, bibliography):
    if os.environ.get("LATEX_STARTER_INTEGRATION") != "1":
        pytest.skip("Opt in with LATEX_STARTER_INTEGRATION=1")
    if not all(shutil.which(tool) for tool in ("xelatex", "latexmk", *(["biber"] if bibliography else []))):
        pytest.skip("External TeX toolchain missing")
    run(["latex-starter", "new", "compiled", "--yes", "--language", language,
         "--structure", "split" if bibliography else "single",
         "--bibliography" if bibliography else "--no-bibliography", "--compile", "--no-open"], tmp_path, app.env)
    pdf = tmp_path / "compiled/build/main.pdf"
    assert pdf.read_bytes().startswith(b"%PDF")
    if bibliography:
        assert (pdf.parent / "main.bbl").is_file()


def test_pipx_reinstall_and_uninstall(tmp_path, offline_env):
    # Independent lifecycle environment: do not invalidate pipx_app's session.
    pytest.importorskip("pipx")
    env = {**offline_env, "PIPX_HOME": str(tmp_path / "home"),
           "PIPX_BIN_DIR": str(tmp_path / "bin"), "PIPX_MAN_DIR": str(tmp_path / "man")}
    run([sys.executable, "-m", "pipx", "install", "--editable", ROOT, "--python", sys.executable], tmp_path, env)
    run([sys.executable, "-m", "pipx", "reinstall", "latex-starter"], tmp_path, env)
    executable = tmp_path / "bin" / ("latex-starter.exe" if os.name == "nt" else "latex-starter")
    run([executable, "--version"], tmp_path, env)
    run([sys.executable, "-m", "pipx", "uninstall", "latex-starter"], tmp_path, env)
    assert not executable.exists()
