"""Helpers for the setup steps: edits that fail loudly when the text they expect isn't there.

Each step runs from the lattice checkout's root. An edit names the exact text it replaces, so a
change upstream before the day stops the run instead of being edited around.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import NoReturn

MIGRATION = Path(__file__).resolve().parent
FILES = MIGRATION / "files"
WORK = Path(os.environ["LATTICE_WORK"])
"""Where import.sh wrote the clones, the commit maps and the lattice checkout."""

PACKAGES = ("artifactr", "reflexr", "evalr", "stackr", "relayr")


def fail(message: str) -> NoReturn:
    """Stop the run."""
    print(f"setup: {message}", file=sys.stderr)
    raise SystemExit(1)


def git(*args: str) -> str:
    """Run git in the checkout; return its output."""
    done = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if done.returncode:
        fail(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout


def replace(path: str | Path, old: str, new: str, *, count: int = 1) -> None:
    """Replace ``old`` with ``new`` in a file, where ``old`` occurs exactly ``count`` times."""
    file = Path(path)
    text = file.read_text()
    found = text.count(old)
    if found != count:
        fail(f"{file}: expected {count} of {old!r}, found {found}")
    file.write_text(text.replace(old, new))


def sub(path: str | Path, pattern: str, new: str, *, count: int = 1) -> None:
    """Replace a regular expression's matches in a file, where it matches exactly ``count`` times."""
    file = Path(path)
    text, found = re.subn(pattern, new, file.read_text(), flags=re.MULTILINE)
    if found != count:
        fail(f"{file}: expected {count} match(es) of {pattern!r}, found {found}")
    file.write_text(text)


def remove(*paths: str) -> None:
    """Remove tracked files or directories, which must exist."""
    for path in paths:
        if not Path(path).exists():
            fail(f"{path} does not exist")
    # --force: a step may remove what it has just moved.
    git("rm", "-r", "--force", "--quiet", *paths)


def move(source: str, destination: str) -> None:
    """``git mv`` a file or directory, creating the destination's parent."""
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    git("mv", source, destination)


def install() -> None:
    """Copy the running step's prepared files (``files/<step>/``) into the checkout."""
    step = Path(sys.argv[0]).stem
    source = FILES / step
    if not source.is_dir():
        fail(f"no prepared files for {step}")
    shutil.copytree(source, Path.cwd(), dirs_exist_ok=True)


def locked(package: str) -> str:
    """The version of a package that the checkout's uv.lock pins."""
    lock = tomllib.loads(Path("uv.lock").read_text())
    for entry in lock["package"]:
        if entry["name"] == package:
            return str(entry["version"])
    fail(f"uv.lock has no {package}")


def run(*command: str, cwd: str | Path | None = None) -> str:
    """Run a command; stop the run if it fails."""
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if done.returncode:
        fail(f"{' '.join(command)}: {done.stdout}{done.stderr}".strip())
    return done.stdout
