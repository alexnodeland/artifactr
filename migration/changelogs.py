"""The changelogs' history, generated once with git-cliff.

See stackr's RFC-0003, Releases and versioning.

git-cliff runs in each package's rewritten clone, so the history is the package's alone, without
the merge that imported it, from the package's directory, which scopes it to that directory.
It uses the package's own cliff.toml, changed only where the import changed the history, and
where release-please takes over:

- tags carry the package's prefix, as in artifactr-v0.1.0, so the headings trim it;
- messages say alexnodeland/<repo>#N where they said #N or "<repo> #N": the preprocessor that
  links a squash commit's pull request matches that form and links it as before, and another
  links every other reference, mid-sentence too, to its repository's issue or pull request;
- the commits cliff.toml skips by SHA have new SHAs, from filter-repo's commit map;
- the release links point at lattice, where the prefixed tags are;
- what no release carries is "Before lattice", not "Unreleased", with no compare link.
  release-please starts from the import, and writes each release above that heading.
"""

import re
from pathlib import Path

from lib import WORK, fail, replace, run

GIT_CLIFF = "2.14.2"
"""The version every package's uv.lock pinned."""

SKIP = re.compile(r'\{ sha = "([0-9a-f]{40})", skip = true \}')


def commit_map(name: str) -> dict[str, str]:
    """filter-repo's map from a package's old commits to their new ones."""
    lines = (WORK / "out" / "commit-map" / name).read_text().splitlines()
    return dict(line.split() for line in lines[1:])


def config(name: str, directory: Path) -> Path:
    """The package's cliff.toml, with the import's changes, written under WORK/out/cliff/."""
    path = WORK / "out" / "cliff" / f"{name}.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((directory / "cliff.toml").read_text())
    replace(path, 'trim_start_matches(pat="v")', f'trim_start_matches(pat="{name}-v")', count=3)
    replace(path, "    ## [Unreleased]\n", "    ## [Before lattice]\n")
    replace(
        path,
        f"            [unreleased]: https://github.com/alexnodeland/{name}/compare/"
        "{{ release.previous.version }}...HEAD\n",
        "",
    )
    replace(
        path,
        f"https://github.com/alexnodeland/{name}/compare/",
        "https://github.com/alexnodeland/lattice/compare/",
    )
    replace(
        path,
        f"https://github.com/alexnodeland/{name}/releases/tag/",
        "https://github.com/alexnodeland/lattice/releases/tag/",
    )
    pull_request = (
        r"    { pattern = '\s*\((\w+\s)?#([0-9]+)\)', replace = "
        f'" ([#${{2}}](https://github.com/alexnodeland/{name}/pull/${{2}}))" }},\n'
    )
    replace(
        path,
        pull_request,
        pull_request.replace("?#([0-9]+)", f"?alexnodeland/{name}#([0-9]+)")
        + r"    { pattern = 'alexnodeland/(\w+)#([0-9]+)', replace = "
        + '"[${1}#${2}](https://github.com/alexnodeland/${1}/issues/${2})" },\n',
    )
    moved = commit_map(name)
    skipped = SKIP.findall(path.read_text())
    for old in skipped:
        if old not in moved:
            fail(f"packages/{name}/cliff.toml skips {old}, which is not in the commit map")
        replace(path, f'sha = "{old}"', f'sha = "{moved[old]}"')
    if skipped:
        print(f"    {name}: {len(skipped)} skipped commits, mapped to their new SHAs")
    return path


def generate(name: str, changelog: Path) -> None:
    """Write a package's changelog, from its history, to a file."""
    directory = WORK / "clones" / name / "packages" / name
    run(
        "uvx",
        f"git-cliff@{GIT_CLIFF}",
        "--config",
        str(config(name, directory)),
        "--tag-pattern",
        f"{name}-v.*",
        "--output",
        str(changelog.resolve()),
        cwd=directory,
    )
    # As `make changelog` wrote it: one newline at the end.
    changelog.write_text(changelog.read_text().rstrip() + "\n")
