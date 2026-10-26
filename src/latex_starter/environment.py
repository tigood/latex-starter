"""Read-only dependency and exact font-family diagnostics."""
from __future__ import annotations

from dataclasses import dataclass
import shutil
import subprocess
import sys


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str
    required: bool = False


@dataclass(frozen=True)
class EnvironmentReport:
    checks: tuple[Check, ...]

    @property
    def ready(self) -> bool:
        return all(c.status == "OK" for c in self.checks if c.required)


def _output(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=10)
    if result.returncode:
        raise OSError(f"Exit {result.returncode}: {result.stderr.strip()[:200]}")
    return result.stdout.strip()


def font_check() -> Check:
    families = ("Noto Serif CJK SC", "Noto Sans CJK SC", "Noto Sans Mono CJK SC")
    fallback = ("FandolSong-Regular.otf", "FandolHei-Regular.otf", "FandolFang-Regular.otf")
    fc, kpse = shutil.which("fc-match"), shutil.which("kpsewhich")
    if not fc and not kpse:
        return Check("CJK fonts", "WARN", "fc-match and kpsewhich absent; font availability unknown", True)
    selected = []
    for family, font_file in zip(families, fallback):
        try:
            # fc-match returns a fallback even when the requested font is absent.
            if fc and family in _output([fc, "-f", "%{family}", family]).split(","):
                selected.append(family)
            elif kpse and _output([kpse, font_file]):
                selected.append(font_file)
            else:
                return Check("CJK fonts", "MISSING", f"Need {family} or {font_file}; install a CJK font yourself", True)
        except (OSError, subprocess.SubprocessError) as error:
            return Check("CJK fonts", "WARN", f"Cannot verify fonts automatically: {error}", True)
    note = " (fc-match unavailable; verified TeX fallback)" if not fc else ""
    return Check("CJK fonts", "OK", ", ".join(selected) + note, True)


def diagnose(language: str = "zh", bibliography: bool = False) -> EnvironmentReport:
    checks = [Check("Python", "OK" if sys.version_info >= (3, 10) else "MISSING",
                    sys.version.split()[0], True)]
    for name, required, version_arg in (
        ("xelatex", True, "--version"), ("latexmk", True, "--version"),
        ("biber", bibliography, "--version"), ("code", False, "--version"),
        ("git", False, "--version"),
    ):
        executable = shutil.which(name)
        if not executable:
            impact = "required for this compilation" if required else "optional for this configuration"
            checks.append(Check(name, "MISSING" if required else "WARN", f"Not on PATH; {impact}", required))
            continue
        try:
            output = _output([executable, version_arg])
            version = next((line for line in output.splitlines() if line.strip()), "Version unavailable")
            checks.append(Check(name, "OK", version, required))
        except (OSError, subprocess.SubprocessError) as error:
            checks.append(Check(name, "WARN", f"Found command but version probe failed: {error}", required))
    if language != "en":
        checks.append(font_check())
    return EnvironmentReport(tuple(checks))
