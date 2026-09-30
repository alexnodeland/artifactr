"""One set of workflows, hooks and repository files.

See stackr's RFC-0003, CI and tooling; Releases and versioning.

The packages' workflows, hooks, Dependabot files, issue forms and pull request templates were
copies of one another, and lattice has one of each. Renovate replaces Dependabot, prek replaces
pre-commit on the same configuration, and release-please replaces git-cliff for releases.
"""

import json
import tomllib
from pathlib import Path

from lib import PACKAGES, git, install, move, remove, replace, run

for name in PACKAGES:
    remove(f"packages/{name}/.github", f"packages/{name}/.pre-commit-config.yaml")
move("packages/artifactr/.editorconfig", ".editorconfig")
for name in ("reflexr", "evalr", "stackr", "relayr"):
    remove(f"packages/{name}/.editorconfig")
install("09-ci")

# prek runs the hooks now; its version, and the workflow linters', come from the root's group.
for name in ("artifactr", "reflexr", "evalr", "relayr"):
    replace(f"packages/{name}/pyproject.toml", '    "pre-commit>=4.6",\n', "")
replace("packages/stackr/pyproject.toml", '  "pre-commit>=4.6.2",\n', "")
replace(
    "pyproject.toml",
    'dev = [\n    "deptry>=0.25",\n    "pyright>=1.1.414",\n    "pytest>=9.1",\n',
    'dev = [\n    "actionlint-py>=1.7.12",\n    "deptry>=0.25",\n    "prek>=0.5.4",\n'
    '    "pyright>=1.1.414",\n    "pytest>=9.1",\n',
)
replace("pyproject.toml", '    "ruff>=0.16",\n]\n', '    "ruff>=0.16",\n    "zizmor>=1.30",\n]\n')
replace(
    "Makefile",
    "install: ## Install every package, dependency group and extra\n"
    "\t$(UV) sync --all-packages --all-groups --all-extras\n",
    "install: ## Install every package, dependency group and extra, and the git hooks\n"
    "\t$(UV) sync --all-packages --all-groups --all-extras\n"
    "\t$(UV) run prek install\n",
)
replace(
    ".devcontainer/post-create.sh",
    "uv sync --all-packages --all-groups --all-extras\n",
    "uv sync --all-packages --all-groups --all-extras\nuv run prek install\n",
)
run("uv", "lock", "--quiet")

# actionlint and zizmor run in CI as well as in the hooks: the root project checks the workflows.
replace(
    "moon.yml",
    "  check:\n",
    """  workflows:
    description: 'Lint the workflows with actionlint and zizmor'
    script: 'uv run actionlint && uv run zizmor --quiet .github/workflows'
    inputs:
      - '.github/workflows/**/*'
      - 'uv.lock'

  check:
""",
)
replace("moon.yml", "      - 'docs'\n", "      - 'docs'\n      - 'workflows'\n")

# release-please: each package's path, with the python release type and a package-name that
# gives its tags their component (artifactr-v0.2.0). The lock records each member's version, so
# a release updates it too. Its bootstrap is the import, so it never reads the old history.
bootstrap = git("rev-list", "--merges", "--max-count=1", "HEAD").strip()
packages: dict[str, object] = {}
manifest: dict[str, str] = {}
for name in PACKAGES:
    project = tomllib.loads(Path(f"packages/{name}/pyproject.toml").read_text())["project"]
    packages[f"packages/{name}"] = {
        "release-type": "python",
        "package-name": name,
        "extra-files": [
            {
                "type": "toml",
                "path": "/uv.lock",
                "jsonpath": f"$.package[?(@.name.value=='{project['name']}')].version",
            }
        ],
    }
    manifest[f"packages/{name}"] = project["version"]
# The packages are pre-1.0, where a breaking change bumps the minor version, as their `!`
# commits always have; release-please's default would release 1.0.0 on the first one.
config = {
    "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
    "bootstrap-sha": bootstrap,
    "bump-minor-pre-major": True,
    "packages": packages,
}
Path("release-please-config.json").write_text(json.dumps(config, indent=2) + "\n")
Path(".release-please-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

# stackr's notes on its tools, now that pre-commit, git-cliff and Zensical are the root's or gone.
replace(
    "packages/stackr/Makefile",
    "# The tools (linters, pre-commit, git-cliff, Zensical) run through uv, so their\n"
    "# versions are the ones in uv.lock.",
    "# The tools (linters and Copier) run through uv, so their versions are the ones in\n"
    "# lattice's uv.lock.",
)
replace(
    "packages/stackr/pyproject.toml",
    "# stackr is not a Python package. This file pins the tools that develop and\n"
    "# validate it (linters, pre-commit, git-cliff, Copier for the application\n"
    "# template, and Zensical for the documentation site), so `make` and CI run the\n"
    "# same versions from uv.lock, as in the rest of the family.\n",
    "# stackr is not a Python package. This file pins the tools that develop and\n"
    "# validate it (linters, and Copier for the application template), so `make` and\n"
    "# CI run the same versions from lattice's uv.lock.\n",
)
