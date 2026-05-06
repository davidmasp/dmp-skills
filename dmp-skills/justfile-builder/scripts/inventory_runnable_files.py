#!/usr/bin/env python3
"""
Summarize runnable project files that are good candidates for Justfile recipes.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


DEFAULT_DIRS = ("scripts", "bin", "tools")
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
}
KNOWN_COMMANDS = {
    ".py": "uv run {path}",
    ".sh": "bash {path}",
    ".bash": "bash {path}",
    ".zsh": "zsh {path}",
    ".ps1": "pwsh -File {path}",
    ".rb": "ruby {path}",
    ".pl": "perl {path}",
    ".js": "node {path}",
    ".ts": "tsx {path}",
    ".nu": "nu {path}",
    ".r": "Rscript {path}",
    ".R": "Rscript {path}",
    ".rmd": "Rscript -e \"rmarkdown::render('{path}')\"",
    ".Rmd": "Rscript -e \"rmarkdown::render('{path}')\"",
    ".qmd": "quarto render {path}",
    ".ipynb": "jupyter nbconvert --to notebook --execute {path}",
    ".typ": "typst compile {path}",
}


def describe_name(path: Path) -> str:
    stem = path.stem.replace("_", " ").replace("-", " ").strip()
    return " ".join(word for word in stem.split() if word)


def command_hint(path: Path) -> str:
    suffix = path.suffix.lower()
    rel = path.as_posix()
    if suffix in KNOWN_COMMANDS:
        return KNOWN_COMMANDS[suffix].format(path=rel)
    if os.access(path, os.X_OK):
        return f"./{rel}"
    return rel


def is_runnable(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() in KNOWN_COMMANDS:
        return True
    return os.access(path, os.X_OK)


def iter_candidates(root: Path, dirs: list[str]) -> list[Path]:
    candidates: list[Path] = []
    for directory in dirs:
        target = root / directory
        if not target.exists() or not target.is_dir():
            continue
        for current_root, subdirs, files in os.walk(target):
            subdirs[:] = [name for name in subdirs if name not in SKIP_DIRS and not name.startswith(".")]
            for filename in files:
                if filename.startswith("."):
                    continue
                path = Path(current_root) / filename
                if is_runnable(path):
                    candidates.append(path)
    return sorted(candidates)


def build_summary(root: Path, dirs: list[str]) -> dict:
    files = []
    for path in iter_candidates(root, dirs):
        relative = path.relative_to(root)
        files.append(
            {
                "path": relative.as_posix(),
                "name": describe_name(relative),
                "extension": path.suffix.lower(),
                "executable": os.access(path, os.X_OK),
                "command_hint": command_hint(relative),
            }
        )
    return {
        "root": str(root),
        "searched_dirs": dirs,
        "count": len(files),
        "files": files,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize runnable files for Justfile generation.",
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Project root to inspect. Defaults to current directory.",
    )
    parser.add_argument(
        "--dirs",
        nargs="+",
        default=list(DEFAULT_DIRS),
        help="Directories to search relative to root.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    summary = build_summary(root, args.dirs)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
