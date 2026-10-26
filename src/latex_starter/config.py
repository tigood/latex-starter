"""One normalized model for CLI parameters and wizard answers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata

from .catalog import FEATURES, Template


def project_slug(name: str) -> str:
    if not isinstance(name, str) or any(c in name for c in "/\\") or name.strip() in {"", ".", ".."}:
        raise ValueError("Project name must be one directory name, without path separators")
    if any(unicodedata.category(c).startswith("C") for c in name):
        raise ValueError("Project name contains control characters")
    slug = re.sub(r"\s+", "-", unicodedata.normalize("NFKC", name).strip()).lower()
    if (not re.fullmatch(r"[^\W_][\w.-]*", slug, re.UNICODE) or slug.endswith(".")
            or len(slug.encode("utf-8")) > 180):
        raise ValueError("Use letters, digits, Unicode letters, hyphens, underscores or dots for the name")
    return slug


@dataclass(frozen=True)
class ProjectConfig:
    project_name: str
    slug: str
    template: str
    language: str
    structure: str
    output_dir: Path
    title: str
    author: str
    institution: str
    features: dict[str, bool]
    compile: bool = False
    open_editor: bool = False
    dry_run: bool = False
    engine: str = "xelatex"

    @property
    def target(self) -> Path:
        return self.output_dir / self.slug


def make_config(template: Template, values: dict) -> ProjectConfig:
    name = values.get("project_name")
    slug = project_slug(name)
    language = values.get("language") or template.default_language
    structure = values.get("structure") or template.default_structure
    if language not in template.supported_languages or structure not in template.supported_structures:
        raise ValueError(f"Language or structure unsupported by {template.id}")
    features = dict(template.defaults)
    for key in FEATURES:
        value = values.get(key)
        if value is not None:
            if type(value) is not bool or (value and not template.features[key]):
                raise ValueError(f"Unsupported feature: {key}")
            features[key] = value
    texts = {key: values.get(key) for key in ("title", "author", "institution")}
    texts["title"] = texts["title"] if texts["title"] is not None else name
    for key, value in texts.items():
        value = "" if value is None else value
        if not isinstance(value, str) or any(unicodedata.category(c).startswith("C") for c in value):
            raise ValueError(f"{key} must be plain text without control characters")
        if key == "title" and not value.strip():
            raise ValueError("Title must not be empty")
        texts[key] = value
    # Resolve only the parent so a final target symlink remains detectable.
    output = Path(values.get("output_dir") or ".").expanduser().resolve()
    return ProjectConfig(name, slug, template.id, language, structure, output,
                         texts["title"], texts["author"], texts["institution"], features,
                         bool(values.get("compile")), bool(values.get("open_editor")),
                         bool(values.get("dry_run")), template.default_engine)
