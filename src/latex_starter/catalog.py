"""Versioned, finite template manifests; no executable hooks or expressions."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from .filesystem import safe_relative

FEATURES = ("bibliography", "figures_tables_examples", "code_listing_example",
            "table_of_contents", "appendix")
LANGUAGES = ("zh", "en", "mixed")
STRUCTURES = ("single", "split")
TEMPLATE_ROOT = Path(__file__).parent / "templates"


@dataclass(frozen=True)
class FileSpec:
    source: Path
    target: str
    when: dict[str, str | bool]


@dataclass(frozen=True)
class Template:
    id: str
    name: str
    description: str
    root: Path
    supported_languages: tuple[str, ...]
    supported_structures: tuple[str, ...]
    default_language: str
    default_structure: str
    default_engine: str
    features: dict[str, bool]
    defaults: dict[str, bool]
    files: tuple[FileSpec, ...]
    schema_version: int = 1


def _read(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read template manifest {path}: {error}") from error


def _files(raw: object, root: Path) -> list[FileSpec]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("Manifest files must be a nonempty list")
    result = []
    for entry in raw:
        if not isinstance(entry, dict) or set(entry) - {"source", "target", "when"}:
            raise ValueError("Invalid file entry")
        source = root / safe_relative(entry.get("source"))
        target = str(safe_relative(entry.get("target")))
        if not source.resolve().is_relative_to(root.resolve()) or not source.is_file():
            raise ValueError(f"Missing or escaping template source: {source}")
        when = entry.get("when", {})
        if not isinstance(when, dict):
            raise ValueError("when must be an object")
        for key, value in when.items():
            if key in FEATURES and type(value) is bool:
                continue
            if key == "language" and value in LANGUAGES:
                continue
            if key == "structure" and value in STRUCTURES:
                continue
            raise ValueError(f"Invalid finite condition: {key}={value!r}")
        result.append(FileSpec(source, target, when))
    return result


def load_template(directory: Path, catalog_root: Path = TEMPLATE_ROOT) -> Template:
    for base, manifest in ((directory, "template.json"), (catalog_root / "_shared", "files.json")):
        if (not base.resolve().is_relative_to(catalog_root.resolve())
                or not (base / manifest).resolve().is_relative_to(base.resolve())):
            raise ValueError(f"Manifest escapes template catalog: {base / manifest}")
    raw = _read(directory / "template.json")
    required = {"schema_version", "id", "name", "description", "supported_languages",
                "supported_structures", "default_language", "default_structure",
                "default_engine", "features", "defaults", "files"}
    if not isinstance(raw, dict) or set(raw) != required:
        raise ValueError(f"Invalid descriptor fields: {directory}")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise ValueError("Unsupported template schema version")
    if (not isinstance(raw["id"], str) or not re.fullmatch(r"[a-z][a-z0-9-]*", raw["id"])
            or raw["id"] != directory.name):
        raise ValueError("Template id must match its directory")
    for key in ("name", "description"):
        if not isinstance(raw[key], str) or not raw[key].strip():
            raise ValueError(f"Invalid {key}")
    for key, allowed in (("languages", LANGUAGES), ("structures", STRUCTURES)):
        values = raw[f"supported_{key}"]
        if (not isinstance(values, list) or not values or
                any(not isinstance(v, str) or v not in allowed for v in values)
                or len(set(values)) != len(values)):
            raise ValueError(f"Invalid supported_{key}")
        default = raw["default_language" if key == "languages" else "default_structure"]
        if default not in values:
            raise ValueError(f"Invalid default for {key}")
    if raw["default_engine"] != "xelatex":
        raise ValueError("Only xelatex is supported in schema 1")
    for key in ("features", "defaults"):
        if (not isinstance(raw[key], dict) or set(raw[key]) != set(FEATURES)
                or any(type(v) is not bool for v in raw[key].values())):
            raise ValueError(f"{key} must declare every feature as a boolean")
    if any(raw["defaults"][k] and not raw["features"][k] for k in FEATURES):
        raise ValueError("Default enables unsupported feature")
    files = _files(_read(catalog_root / "_shared" / "files.json"), catalog_root / "_shared")
    files += _files(raw["files"], directory)
    targets = [f.target for f in files]
    if any(Path(target).parts[0] == ".latex-starter.json" for target in targets):
        raise ValueError("Reserved metadata target: .latex-starter.json")
    if len(targets) != len(set(targets)):
        raise ValueError("Duplicate target path")
    if any(a != b and Path(a) in Path(b).parents for a in targets for b in targets):
        raise ValueError("File/directory target collision")
    return Template(raw["id"], raw["name"], raw["description"], catalog_root,
                    tuple(raw["supported_languages"]), tuple(raw["supported_structures"]),
                    raw["default_language"], raw["default_structure"], raw["default_engine"],
                    raw["features"], raw["defaults"], tuple(files))


def discover(root: Path = TEMPLATE_ROOT) -> dict[str, Template]:
    templates = {}
    for path in sorted(root.glob("*/template.json")):
        if path.parent.is_symlink():
            raise ValueError(f"Symlink template directory: {path.parent}")
        template = load_template(path.parent, root)
        templates[template.id] = template
    if not templates:
        raise ValueError(f"No templates found in {root}")
    return templates
