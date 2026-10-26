"""Command routing and orchestration; reusable logic lives in separate modules."""
from __future__ import annotations

import argparse
import sys

from jinja2 import TemplateError

from . import __version__
from .catalog import FEATURES, LANGUAGES, STRUCTURES, discover
from .compiler import compile_project, open_project
from .config import make_config
from .environment import EnvironmentReport, diagnose
from .filesystem import check_target, write_project
from .renderer import render
from .wizard import collect, yes_no


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="latex-starter", description="Safely create local XeLaTeX projects / 创建 LaTeX 项目")
    root.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List built-in templates")
    doctor = commands.add_parser("doctor", help="Check commands and fonts without installing anything")
    doctor.add_argument("--language", choices=LANGUAGES, default="zh")
    doctor.add_argument("--bibliography", action="store_true", help="Require Biber")
    new = commands.add_parser("new", help="Create a project (interactive unless --yes)")
    new.add_argument("project_name", nargs="?")
    new.add_argument("--template", help="Template id; see latex-starter list")
    new.add_argument("--language", choices=LANGUAGES)
    new.add_argument("--structure", choices=STRUCTURES)
    for option in ("output-dir", "title", "author", "institution"):
        new.add_argument("--" + option)
    for feature in FEATURES:
        new.add_argument("--" + feature.replace("_", "-"), dest=feature,
                         action=argparse.BooleanOptionalAction, default=None)
    new.add_argument("--compile", action=argparse.BooleanOptionalAction, default=None)
    new.add_argument("--open", dest="open_editor", action=argparse.BooleanOptionalAction, default=None,
                     help="Open VS Code only after successful compilation")
    new.add_argument("--dry-run", action="store_true", help="Preview all files; no writes, builds or editor launches")
    new.add_argument("--yes", action="store_true", help="Use descriptor defaults without prompts; project name required")
    return root


def show_environment(report: EnvironmentReport) -> None:
    for check in report.checks:
        print(f"{check.status:7} {check.name}: {check.detail}")
    print("Environment: " + ("available for compilation" if report.ready else "not fully verified / dependencies missing"))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    stage = args.command
    try:
        if args.command == "doctor":
            report = diagnose(args.language, args.bibliography)
            show_environment(report)
            return 0 if report.ready else 1
        templates = discover()
        if args.command == "list":
            for template in templates.values():
                print(f"{template.id:20} {template.name}: {template.description} "
                      f"[engine={template.default_engine}; optional=biber,CJK fonts]")
            return 0
        values = vars(args).copy()
        if values.get("template") and values["template"] not in templates:
            raise ValueError(f"Unknown template {values['template']!r}; run latex-starter list")
        if not args.yes:
            if not sys.stdin.isatty():
                raise ValueError("Interactive new requires a terminal; use --yes PROJECT_NAME for scripts")
            values, template = collect(values, templates)
        else:
            template = templates[values.get("template") or "academic-article"]
        config = make_config(template, values)
        stage = f"planning {config.target}"
        check_target(config.target)
        files = render(template, config)
        print(f"Target: {config.target}\nTemplate: {config.template}; language={config.language}; structure={config.structure}")
        print("Features: " + ", ".join(k for k, v in config.features.items() if v))
        print(f"Title: {config.title}; author={config.author}; institution={config.institution}")
        print(f"Compile: {config.compile}; open VS Code: {config.open_editor}")
        for path in sorted(files):
            print(f"  {path}")
        if config.dry_run:
            print("Dry run: no files written; no compilation or editor launch")
            return 0
        if not args.yes and not yes_no("Create this project / 确认创建"):
            print("Cancelled; no files written")
            return 0
        stage = f"creating {config.target}"
        write_project(config.target, files)
        print(f"Created: {config.target}")
        stage = f"diagnosing {config.target}"
        report = diagnose(config.language, config.features["bibliography"])
        show_environment(report)
        exit_code = 0
        compiled = False
        if config.compile:
            stage = f"compiling {config.target}"
            result = compile_project(config.target, config.features["bibliography"])
            compiled = result.success
            print(result.summary)
            if result.log.exists():
                print(f"Build log: {result.log}")
            if compiled:
                print(f"PDF: {result.pdf}")
            elif result.returncode is not None or result.log.exists():
                exit_code = 1
            # Missing external tools do not undo successful creation.
        else:
            print("Compilation: not requested; project not compile-verified")
        if config.open_editor:
            if compiled:
                opened, message = open_project(config.target)
                print(message)
                if not opened:
                    exit_code = 1
            else:
                print("VS Code not opened: no successful compilation in this run")
        print("Next: see generated README.md for the build command")
        return exit_code
    except (OSError, ValueError, TemplateError) as error:
        print(f"Error during {stage}: {error}\nCheck the path/configuration and retry; existing user files are preserved.", file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        print("Cancelled by input interruption", file=sys.stderr)
        return 130
