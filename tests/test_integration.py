"""Optional real builds, always confined to pytest temporary directories."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from latex_starter.catalog import discover
from latex_starter.compiler import BUILD_FLAGS, compile_project
from latex_starter.config import make_config
from latex_starter.filesystem import write_project
from latex_starter.renderer import render

pytestmark = [pytest.mark.integration,
              pytest.mark.skipif(os.environ.get("LATEX_STARTER_INTEGRATION") != "1", reason="Opt in with LATEX_STARTER_INTEGRATION=1")]


def require_tools(bibliography):
    for tool in ("xelatex", "latexmk", *(["biber"] if bibliography else [])):
        if not shutil.which(tool):
            pytest.skip(f"Missing external dependency: {tool}")


@pytest.mark.parametrize("template_id,language,structure,bibliography", [
    ("academic-article", "zh", "split", True),
    ("academic-article", "en", "single", False),
    ("academic-article", "zh", "single", False),
    ("course-report", "mixed", "split", True),
    ("notes", "zh", "single", False),
])
def test_real_compile(tmp_path, template_id, language, structure, bibliography):
    require_tools(bibliography)
    template = discover()[template_id]
    config = make_config(template, dict(project_name="test", output_dir=tmp_path / "父目录 with spaces",
        language=language, structure=structure, bibliography=bibliography,
        title=r"Title & % # _ { } $ ~ ^ \ example", author="A & B"))
    write_project(config.target, render(template, config))
    result = compile_project(config.target, bibliography)
    assert result.success, result.log.read_text()[-10000:]
    assert result.pdf.is_file()
    assert not list(config.target.glob("*.aux"))
    log = (config.target / "build/main.log").read_text(errors="replace")
    assert "undefined citations" not in log
    if bibliography:
        assert (config.target / "build/main.bbl").is_file()
        assert "knuth1984" in (config.target / "build/main.bbl").read_text()


def test_actual_workshop_recipe_command(tmp_path):
    require_tools(True)
    template = discover()["academic-article"]
    config = make_config(template, dict(project_name="recipe", output_dir=tmp_path / "with spaces", language="zh"))
    files = render(template, config)
    write_project(config.target, files)
    settings = json.loads(files[".vscode/settings.json"])
    tool = settings["latex-workshop.latex.tools"][0]
    for flag in BUILD_FLAGS:
        assert flag in tool["args"]
    args = [arg.replace("%DIR%", str(config.target)).replace("%DOC%", str(config.target / "main")) for arg in tool["args"]]
    # Run the exact generated recipe, expanded as LaTeX Workshop does, even
    # when the original working directory is outside the generated project.
    result = subprocess.run([tool["command"], *args], cwd=tmp_path, capture_output=True,
                            text=True, errors="replace", timeout=180)
    assert result.returncode == 0, result.stdout[-10000:] + result.stderr
    assert (config.target / "build/main.pdf").is_file()
    assert (config.target / "build/main.bbl").is_file()
    assert not list(tmp_path.glob("*.aux"))
