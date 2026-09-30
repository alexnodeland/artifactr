"""moon: the task runner over every project (stackr's RFC-0003, moon; D2, D3)."""

from pathlib import Path

from lib import install, remove, replace, run

install()

# The libraries' Makefiles become moon tasks: python.yml's lint, typecheck, test and format for
# every Python project, and each project's own (schema, dashboards, pg-up, pg-down, app-up,
# test-pg) in its moon.yml. `make changelog` retires with git-cliff, and the docs build is the
# root's.
for name in ("artifactr", "reflexr", "evalr", "relayr"):
    remove(f"packages/{name}/Makefile")

# stackr keeps its Makefile (D2), apart from `install`: a `uv sync` from stackr's directory would
# leave the workspace's one environment with stackr's tools alone. The root's `make install`
# sets up everything.
makefile = "packages/stackr/Makefile"
replace(makefile, ".PHONY: help install env ", ".PHONY: help env ")
replace(
    makefile,
    "install: ## Install the development tools and the git hooks\n"
    "\t$(UV) sync\n"
    "\t$(UV) run pre-commit install --hook-type pre-commit --hook-type commit-msg\n\n",
    "",
)
# Its reference page lists the Makefile's targets, from the Makefile.
run(
    "uv",
    "run",
    "--quiet",
    "--no-project",
    "--with",
    "pyyaml",
    "python",
    "scripts/docs-reference",
    cwd="packages/stackr",
)

gitignore = Path(".gitignore")
gitignore.write_text(gitignore.read_text() + "\n# moon's cache\n.moon/cache/\n")
