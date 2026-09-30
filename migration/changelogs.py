"""The changelogs' history, generated once with git-cliff.

See stackr's RFC-0003, Releases and versioning.

git-cliff runs in each package's rewritten clone, so the history is the package's alone, without
the merge that imported it, from the package's directory, which scopes it to that directory.
It uses the package's own cliff.toml, changed only where the import changed the history:

- tags carry the package's prefix, as in artifactr-v0.1.0, so the headings trim it;
- messages say alexnodeland/<name>#N where they said #N, so the preprocessor that links a pull
  request matches that form, and links it as before;
- the commits cliff.toml skips by SHA have new SHAs, from filter-repo's commit map;
- the release and compare links point at lattice, where the prefixed tags are.
"""

import re
import tempfile
from pathlib import Path

from lib import WORK, fail, replace, run

GIT_CLIFF = "2.14.2"
"""The version every package's uv.lock pinned."""

SKIP = re.compile(r'\{ sha = "([0-9a-f]{40})", skip = true \}')


def commit_map(name: str) -> dict[str, str]:
    """filter-repo's map from a package's old commits to their new ones."""
    lines = (WORK / "out" / "commit-map" / name).read_text().splitlines()
    return dict(line.split() for line in lines[1:])


def config(name: str, directory: Path) -> str:
    """The package's cliff.toml, with the import's changes."""
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as file:
        path = Path(file.name)
    path.write_text((directory / "cliff.toml").read_text())
    replace(path, 'trim_start_matches(pat="v")', f'trim_start_matches(pat="{name}-v")', count=3)
    replace(
        path,
        f"https://github.com/alexnodeland/{name}/compare/",
        "https://github.com/alexnodeland/lattice/compare/",
        count=2,
    )
    replace(
        path,
        f"https://github.com/alexnodeland/{name}/releases/tag/",
        "https://github.com/alexnodeland/lattice/releases/tag/",
    )
    replace(
        path,
        r"{ pattern = '\s*\((\w+\s)?#([0-9]+)\)', ",
        rf"{{ pattern = '\s*\((\w+\s)?alexnodeland/{name}#([0-9]+)\)', ",
    )
    moved = commit_map(name)
    skipped = SKIP.findall(path.read_text())
    for old in skipped:
        if old not in moved:
            fail(f"packages/{name}/cliff.toml skips {old}, which is not in the commit map")
        replace(path, f'sha = "{old}"', f'sha = "{moved[old]}"')
    if skipped:
        print(f"    {name}: {len(skipped)} skipped commits, mapped to their new SHAs")
    return str(path)


def generate(name: str, changelog: Path) -> None:
    """Write a package's changelog, from its history, to a file."""
    directory = WORK / "clones" / name / "packages" / name
    run(
        "uvx",
        f"git-cliff@{GIT_CLIFF}",
        "--config",
        config(name, directory),
        "--tag-pattern",
        f"{name}-v.*",
        "--output",
        str(changelog.resolve()),
        cwd=directory,
    )
    # As `make changelog` wrote it: one newline at the end.
    changelog.write_text(changelog.read_text().rstrip() + "\n")
