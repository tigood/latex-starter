import json
from pathlib import Path
import shutil

import pytest

from latex_starter.catalog import discover, TEMPLATE_ROOT


def test_discover():
    assert set(discover()) == {"academic-article", "course-report", "notes"}


@pytest.fixture
def catalog(tmp_path):
    root = tmp_path / "templates"
    shutil.copytree(TEMPLATE_ROOT, root)
    return root


@pytest.mark.parametrize("mutation", [
    {"schema_version": 2}, {"schema_version": True}, {"id": "other"}, {"name": ""},
    {"unknown": True}, {"default_language": "xx"}, {"default_engine": "lualatex"},
    {"supported_languages": ["en", "en"]}, {"supported_languages": "en"},
    {"features": {"bibliography": "yes"}}, {"files": []},
    {"files": [{"source": "../escape", "target": "main.tex"}]},
    {"files": [{"source": "files/main.tex.j2", "target": "/escape"}]},
    {"files": [{"source": "files/main.tex.j2", "target": "x", "when": {"exec": "whoami"}}]},
    {"files": [{"source": "files/main.tex.j2", "target": "x", "when": {"bibliography": "true"}}]},
    {"files": [{"source": "files/main.tex.j2", "target": "README.md"}]},
    {"files": [{"source": "files/main.tex.j2", "target": "README.md/sub"}]},
    {"files": [{"source": "files/main.tex.j2", "target": ".latex-starter.json/sub"}]},
])
def test_reject_invalid_schema(catalog, mutation):
    path = catalog / "notes/template.json"
    data = json.loads(path.read_text())
    data.update(mutation)
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        discover(catalog)


def test_reject_symlink_source(catalog, tmp_path):
    source = catalog / "notes/files/main.tex.j2"
    source.unlink()
    outside = tmp_path / "secret"
    outside.write_text("not a template")
    source.symlink_to(outside)
    with pytest.raises(ValueError):
        discover(catalog)


def test_reject_symlink_manifest(catalog, tmp_path):
    path = catalog / "notes/template.json"
    outside = tmp_path / "outside.json"
    outside.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(ValueError):
        discover(catalog)


def test_reject_escaping_shared_directory(catalog, tmp_path):
    outside = tmp_path / "outside-shared"
    (catalog / "_shared").rename(outside)
    (catalog / "_shared").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        discover(catalog)


def test_new_descriptor_discovered_without_cli_changes(catalog):
    shutil.copytree(catalog / "notes", catalog / "new-template")
    path = catalog / "new-template/template.json"
    data = json.loads(path.read_text())
    data["id"] = "new-template"
    path.write_text(json.dumps(data))
    assert "new-template" in discover(catalog)


def test_unlisted_file_not_copied(catalog):
    from latex_starter.config import make_config
    from latex_starter.renderer import render
    (catalog / "notes/files/private.txt").write_text("ignore")
    template = discover(catalog)["notes"]
    files = render(template, make_config(template, {"project_name": "test"}))
    assert not any("private" in name for name in files)
