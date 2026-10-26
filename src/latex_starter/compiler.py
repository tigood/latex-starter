"""Known build command and honest exit-code/PDF result handling."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

# Shared by terminal, generated README and LaTeX Workshop recipe.
BUILD_FLAGS = ("-xelatex", "-interaction=nonstopmode", "-halt-on-error",
               "-file-line-error", "-synctex=1", "-outdir=build")


def build_command() -> list[str]:
    return ["latexmk", "-norc", "-r", ".latexmkrc", *BUILD_FLAGS, "main.tex"]


@dataclass(frozen=True)
class BuildResult:
    success: bool
    summary: str
    pdf: Path
    log: Path
    returncode: int | None


def compile_project(project: Path, bibliography: bool = False, timeout: int = 180) -> BuildResult:
    pdf = project / "build/main.pdf"
    log = project / "build/latex-starter-compile.log"
    missing = [name for name in ("latexmk", "xelatex", *(["biber"] if bibliography else []))
               if not shutil.which(name)]
    if missing:
        return BuildResult(False, "Compilation not run; missing: " + ", ".join(missing), pdf, log, None)
    log.parent.mkdir(exist_ok=True)
    try:
        result = subprocess.run(build_command(), cwd=project, capture_output=True,
                                text=True, errors="replace", timeout=timeout)
        output = result.stdout + "\n" + result.stderr
        log.write_text(output, encoding="utf-8")
        success = result.returncode == 0 and pdf.is_file() and pdf.stat().st_size > 0
        errors = [line.strip() for line in output.splitlines()
                  if line.startswith("!") or "error" in line.lower()]
        detail = errors[-1][:300] if errors else f"exit={result.returncode}, PDF present={pdf.is_file()}"
        return BuildResult(success, "Compilation succeeded" if success else f"Compilation failed: {detail}",
                           pdf, log, result.returncode)
    except (OSError, subprocess.SubprocessError) as error:
        output = ""
        if isinstance(error, subprocess.TimeoutExpired):
            for value in (error.stdout, error.stderr):
                if value:
                    output += value.decode(errors="replace") if isinstance(value, bytes) else value
        log.write_text(output + f"\nCompilation interrupted: {error}\n", encoding="utf-8")
        return BuildResult(False, f"Compilation interrupted: {error}", pdf, log, None)


def open_project(project: Path) -> tuple[bool, str]:
    code = shutil.which("code")
    if not code:
        return False, "VS Code not opened: code command is not on PATH"
    try:
        result = subprocess.run([code, str(project)], capture_output=True, text=True,
                                errors="replace", timeout=20)
        return result.returncode == 0, "VS Code opened" if result.returncode == 0 else f"VS Code failed: {result.stderr.strip()}"
    except (OSError, subprocess.SubprocessError) as error:
        return False, f"VS Code not opened: {error}"
