"""PyInstaller entry point; keep runtime CLI logic in its existing module."""
from latex_starter.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
