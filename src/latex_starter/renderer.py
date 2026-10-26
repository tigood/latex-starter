"""Render explicit manifest files in memory; never write or execute templates."""
from __future__ import annotations

from dataclasses import asdict
import json

from jinja2 import FileSystemLoader, StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

from . import __version__
from .catalog import Template
from .config import ProjectConfig
from .compiler import BUILD_FLAGS, build_command

_ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
            "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
            "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def latex_escape(text: str) -> str:
    return "".join(_ESCAPES.get(char, char) for char in text)


def render(template: Template, config: ProjectConfig) -> dict[str, bytes]:
    env = SandboxedEnvironment(loader=FileSystemLoader(str(template.root)),
                              undefined=StrictUndefined, autoescape=False,
                              variable_start_string="<<", variable_end_string=">>",
                              keep_trailing_newline=True)
    env.filters["tex"] = latex_escape
    env.filters["json"] = lambda value: json.dumps(value, ensure_ascii=False)
    context = asdict(config)
    context.update(config.features)
    context.update(version=__version__, chinese=config.language != "en")
    context.update(build_command=" ".join(build_command()),
                   workshop_args=["-cd", "-norc", "-r", "%DIR%/.latexmkrc", *BUILD_FLAGS, "%DOC%"])
    files = {}
    for entry in template.files:
        if not all(context.get(key) == value for key, value in entry.when.items()):
            continue
        if entry.source.suffix == ".j2":
            source = entry.source.relative_to(template.root).as_posix()
            data = env.get_template(source).render(**context).encode("utf-8")
        else:
            data = entry.source.read_bytes()
        files[entry.target] = data
    metadata = {"generator": "latex-starter", "generator_version": __version__,
                "template": template.id, "template_schema_version": template.schema_version,
                "language": config.language, "structure": config.structure,
                "engine": config.engine, "features": config.features,
                "bibliography_backend": "biber" if config.features["bibliography"] else None}
    if ".latex-starter.json" in files:
        raise ValueError("Reserved metadata target: .latex-starter.json")
    files[".latex-starter.json"] = (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode()
    return files
