"""Build an experimental native executable and smoke-test it outside the repo.

Install .[distribution] first. This builds only for the current host OS/CPU.
No TeX programs, fonts, or VS Code installation are included.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import platform
import subprocess
import sys
import tempfile


def build(output_dir: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    tag = f"{platform.system().lower()}-{platform.machine().lower()}"
    output_dir = output_dir.resolve()
    destination = output_dir / tag
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
        "--name", "latex-starter", "--collect-data", "latex_starter",
        "--paths", str(root / "src"), "--distpath", str(destination),
        "--workpath", str(output_dir / ".build" / tag),
        "--specpath", str(output_dir / ".spec" / tag),
        str(root / "packaging" / "entrypoint.py"),
    ], cwd=root, check=True)
    binary = destination / ("latex-starter.exe" if platform.system() == "Windows" else "latex-starter")
    smoke_test(binary)
    print(f"Experimental executable verified on this host: {binary}")
    print("External dependencies remain required: XeLaTeX, latexmk, optional Biber/CJK fonts.")
    return binary


def smoke_test(binary: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="latex-starter-frozen-smoke-") as temp:
        cwd = Path(temp)
        for args in (["--help"], ["--version"], ["list"]):
            subprocess.run([str(binary), *args], cwd=cwd, check=True, timeout=60)
        for template in ("academic-article", "course-report", "notes"):
            subprocess.run([str(binary), "new", template, "--yes", "--template", template,
                            "--language", "en", "--no-compile", "--no-open"],
                           cwd=cwd, check=True, timeout=90)
            if not (cwd / template / "main.tex").is_file():
                raise RuntimeError(f"Frozen template missing: {template}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "dist" / "experimental")
    args = parser.parse_args()
    build(args.output_dir)


if __name__ == "__main__":
    main()
