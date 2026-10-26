"""Fast regressions for package-relative resources, independent of cwd."""
from importlib import resources

import pytest

from latex_starter.catalog import TEMPLATE_ROOT, discover
from latex_starter.config import make_config
from latex_starter.renderer import render


def test_templates_are_package_resources():
    packaged = resources.files("latex_starter").joinpath("templates")
    for template_id, template in discover().items():
        assert packaged.joinpath(template_id, "template.json").is_file()
        for entry in template.files:
            relative = entry.source.relative_to(TEMPLATE_ROOT)
            assert packaged.joinpath(*relative.parts).read_bytes() == entry.source.read_bytes()


@pytest.mark.parametrize("template_id", ["academic-article", "course-report", "notes"])
def test_source_templates_from_unrelated_cwd(tmp_path, monkeypatch, template_id):
    monkeypatch.chdir(tmp_path)
    template = discover()[template_id]
    config = make_config(template, {"project_name": "outside", "bibliography": True})
    files = render(template, config)
    assert "main.tex" in files and "references/references.bib" in files
    assert not list(tmp_path.iterdir())
