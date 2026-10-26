"""Path validation and staged, exclusive project publication."""
from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import tempfile


def safe_relative(value: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError(f"Unsafe manifest path: {value!r}")
    path = PurePosixPath(value)
    if (path.is_absolute() or PureWindowsPath(value).drive
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise ValueError(f"Unsafe manifest path: {value!r}")
    return Path(*path.parts)


def check_target(target: Path) -> None:
    if target.is_symlink():
        raise ValueError(f"Target is a symlink: {target}")
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ValueError(f"Target must be absent or empty; refusing overwrite: {target}")


def write_project(target: Path, files: dict[str, bytes]) -> None:
    """Render first, stage all bytes, then publish with exclusive file creation.

    Only paths created by this operation are removed on failure. Unknown files
    appearing during publication are never overwritten or recursively deleted.
    """
    check_target(target)
    paths = {name: safe_relative(name) for name in files}
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".latex-starter-", dir=target.parent) as temp:
        stage = Path(temp)
        for name, relative in paths.items():
            dest = stage / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(files[name])
        check_target(target)
        created_dirs: list[Path] = []
        created_files: list[Path] = []
        try:
            if not target.exists():
                target.mkdir()
                created_dirs.append(target)
            for name, relative in paths.items():
                dest = target / relative
                for parent in reversed(dest.parents):
                    if parent == target or target in parent.parents:
                        if parent.is_symlink():
                            raise ValueError(f"Symlink encountered during publication: {parent}")
                        if not parent.exists():
                            parent.mkdir()
                            created_dirs.append(parent)
                with dest.open("xb") as stream:
                    created_files.append(dest)
                    stream.write((stage / relative).read_bytes())
        except BaseException:
            for path in reversed(created_files):
                path.unlink(missing_ok=True)
            for path in reversed(created_dirs):
                try:
                    path.rmdir()
                except OSError:
                    pass
            raise
