from dataclasses import replace
import json
from pathlib import Path

import pytest

from latex_starter.catalog import discover, FEATURES
from latex_starter.config import make_config, project_slug
from latex_starter.filesystem import check_target, safe_relative, write_project
from latex_starter.renderer import latex_escape, render


@pytest.fixture
def templates():
    return discover()


@pytest.mark.parametrize("template_id", ["academic-article", "course-report", "notes"])
@pytest.mark.parametrize("language", ["zh", "en", "mixed"])
@pytest.mark.parametrize("structure", ["single", "split"])
@pytest.mark.parametrize("bibliography", [True, False])
def test_generation_matrix(templates, tmp_path, template_id, language, structure, bibliography):
    template = templates[template_id]
    config = make_config(template, dict(project_name="项目 With Spaces", output_dir=tmp_path,
                                      language=language, structure=structure, bibliography=bibliography))
    files = render(template, config)
    write_project(config.target, files)
    main = files["main.tex"].decode()
    source = "\n".join(v.decode() for k, v in files.items() if k.endswith(".tex"))
    assert ("references/references.bib" in files) is bibliography
    assert ("\\autocite" in source) is bibliography
    assert ("\\printbibliography" in source) is bibliography
    assert ("\\usepackage{xeCJK}" in main) is (language != "en")
    assert ("\\input{sections/01_introduction}" in main) is (structure == "split")
    assert ("sections/01_introduction.tex" in files) is (structure == "split")
    metadata = json.loads(files[".latex-starter.json"])
    assert metadata["language"] == language
    assert metadata["bibliography_backend"] == ("biber" if bibliography else None)
    assert str(tmp_path) not in files[".latex-starter.json"].decode()
    assert config.slug == "项目-with-spaces"
    assert not (config.target / "build").exists()
    settings = json.loads(files[".vscode/settings.json"])
    assert settings["latex-workshop.latex.outDir"] == "%DIR%/build"


@pytest.mark.parametrize("feature,marker", [("bibliography", "\\printbibliography"),
    ("figures_tables_examples", "\\begin{figure}"), ("code_listing_example", "\\begin{lstlisting}"),
    ("table_of_contents", "\\tableofcontents"), ("appendix", "\\appendix")])
def test_features_are_independent(templates, feature, marker):
    template = templates["notes"]
    for enabled in (True, False):
        config = make_config(template, {"project_name": "test", **dict.fromkeys(FEATURES, False), feature: enabled})
        source = render(template, config)["main.tex"].decode()
        assert (marker in source) is enabled


def test_special_characters(templates):
    text = r"A & B % # _ { } $ ~ ^ \cmd"
    config = make_config(templates["notes"], dict(project_name="test", title=text, author=text, institution=text))
    source = render(templates["notes"], config)["main.tex"].decode()
    assert source.count(latex_escape(text)) == 3
    assert latex_escape(r"\&{}") == r"\textbackslash{}\&\{\}"


@pytest.mark.parametrize("name", ["", ".", "..", "../foo", "/tmp/x", "x/y", "x\\y", "-bad", "a\x00b", "a\nb", "name."])
def test_invalid_names(name):
    with pytest.raises(ValueError):
        project_slug(name)


@pytest.mark.parametrize("path", ["../x", "/tmp/x", "a/../b", "a//b", "a/./b", "C:/x", "C:x", "a\\b", "", "a/"])
def test_manifest_paths(path):
    with pytest.raises(ValueError):
        safe_relative(path)


def test_defaults_and_invalid_config(templates):
    template = templates["notes"]
    config = make_config(template, {"project_name": "Test"})
    assert config.structure == template.default_structure
    assert config.features == template.defaults
    for values in ({"language": "xx"}, {"structure": "bad"}, {"title": ""}, {"title": "a\nb"}, {"bibliography": "yes"}):
        with pytest.raises(ValueError):
            make_config(template, {"project_name": "test", **values})
    limited = replace(template, features=dict.fromkeys(FEATURES, False))
    with pytest.raises(ValueError):
        make_config(limited, {"project_name": "test", "bibliography": True})


def test_refuse_nonempty_and_symlink(tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    original = target / "paper.tex"
    original.write_text("private")
    with pytest.raises(ValueError):
        write_project(target, {"paper.tex": b"replaced"})
    assert original.read_text() == "private"
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError):
        check_target(link)
    broken = tmp_path / "broken"
    broken.symlink_to(tmp_path / "absent")
    with pytest.raises(ValueError):
        check_target(broken)


def test_empty_directory_and_spaces(tmp_path):
    target = tmp_path / "父目录 with spaces" / "项目"
    target.mkdir(parents=True)
    write_project(target, {"sections/one.tex": b"example"})
    assert (target / "sections/one.tex").read_bytes() == b"example"
    assert not list(target.parent.glob(".latex-starter-*"))


def test_publication_rolls_back_own_files_only(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.mkdir()
    original_open = Path.open

    def fail(path, mode="r", *args, **kwargs):
        if path == target / "second" and mode == "xb":
            (target / "other-user-file").write_text("keep")
            raise OSError("simulated publication failure")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail)
    with pytest.raises(OSError):
        write_project(target, {"first": b"one", "second": b"two"})
    assert not (target / "first").exists()
    assert (target / "other-user-file").read_text() == "keep"
    assert not list(tmp_path.glob(".latex-starter-*"))
