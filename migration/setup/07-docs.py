"""One documentation site for the family (stackr's RFC-0003, Docs).

Each package's pages move to docs/<package>/, with their history, and one mkdocs.yml builds the
site. A folder's .nav.yml orders its section: each package's is its old mkdocs.yml's nav. The
contributing guide, code of conduct, security policy and license exist once, at the root, and
each package keeps its changelog page.
"""

import re
import shutil
from pathlib import Path

import yaml

from lib import PACKAGES, install, move, remove, replace, run, sub

MERGED = ("contributing", "code-of-conduct", "security", "license")
"""The project pages that exist once, at the family's level, and leave each package's section."""

for name in PACKAGES:
    move(f"packages/{name}/docs", f"docs/{name}")


def nav_file(name: str, nav: list[object]) -> None:
    """Write a package's .nav.yml."""
    body = yaml.safe_dump({"nav": nav}, sort_keys=False, allow_unicode=True, width=100)
    Path(f"docs/{name}/.nav.yml").write_text(
        f"# {name}'s section of the site, in order. Paths are from docs/{name}/.\n{body}"
    )


def without_merged(items: list[object]) -> list[object]:
    """A nav without the project pages the family's section now holds."""
    kept: list[object] = []
    for item in items:
        if isinstance(item, dict):
            [(title, value)] = item.items()
            if isinstance(value, list):
                kept.append({title: without_merged(value)})
            elif value not in {f"project/{page}.md" for page in MERGED}:
                kept.append(item)
        else:
            kept.append(item)
    return kept


for name in ("artifactr", "reflexr", "evalr", "stackr"):
    config = yaml.safe_load(Path(f"packages/{name}/mkdocs.yml").read_text())
    nav_file(name, without_merged(config["nav"]))
    remove(f"packages/{name}/mkdocs.yml")
    for page in MERGED:
        remove(f"docs/{name}/project/{page}.md")

# relayr's foundation had no site yet: its section lists its decisions, its plan and its brand.
# Its accepted ADRs link to an index of its RFCs and to a brand page, which the foundation hadn't
# written; they are added (files/07-docs/docs/relayr/), so the one strict build holds.
relayr = Path("docs/relayr")
nav_file(
    "relayr",
    [
        {
            "Decisions": [
                "adr/README.md",
                *sorted(str(path.relative_to(relayr)) for path in relayr.glob("adr/0*.md")),
                "adr/template.md",
            ]
        },
        {
            "RFCs": [
                "rfcs/README.md",
                *sorted(str(path.relative_to(relayr)) for path in relayr.glob("rfcs/0*.md")),
                "rfcs/template.md",
            ]
        },
        {"Brand": "assets/brand/README.md"},
    ],
)

# Pages include files by their path from the repository's root now, and a link to a project
# page that moved to the family's section goes up one more level.
for name in PACKAGES:
    for page in sorted(Path(f"docs/{name}").rglob("*.md")):
        text = page.read_text()
        text = re.sub(r'--8<-- "([^"]+)"', rf'--8<-- "packages/{name}/\1"', text)
        text = re.sub(
            rf"\]\(((?:\.\./)*)project/({'|'.join(MERGED)})\.md",
            r"](\1../project/\2.md",
            text,
        )
        page.write_text(text)

# ─── the family's project files ───────────────────────────────────────────────
# One contributing guide, code of conduct and security policy, at the root: artifactr's move
# there with their history and absorb the others. Each package keeps its LICENSE, which its
# wheel and sdist ship, and the root has the same one.

move("packages/artifactr/CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.md")
replace(
    "CODE_OF_CONDUCT.md",
    "https://github.com/alexnodeland/artifactr/security/advisories/new",
    "https://github.com/alexnodeland/lattice/security/advisories/new",
)
move("packages/artifactr/CONTRIBUTING.md", "CONTRIBUTING.md")
move("packages/artifactr/SECURITY.md", "SECURITY.md")
for name in ("reflexr", "evalr", "stackr"):
    remove(
        f"packages/{name}/CODE_OF_CONDUCT.md",
        f"packages/{name}/CONTRIBUTING.md",
        f"packages/{name}/SECURITY.md",
    )
shutil.copyfile("packages/artifactr/LICENSE", "LICENSE")
install("07-docs")

# ─── the site's scripts ───────────────────────────────────────────────────────
# The list check was one file in five packages; the Sphinx-roles extension was two copies of one
# file, which one build now runs over every package.

move("packages/artifactr/scripts/check_site.py", "scripts/check_site.py")
for name in ("reflexr", "evalr", "stackr", "relayr"):
    remove(f"packages/{name}/scripts/check_site.py")
move("packages/artifactr/scripts/griffe_sphinx_roles.py", "scripts/griffe_sphinx_roles.py")
remove("packages/reflexr/scripts/griffe_sphinx_roles.py")
griffe = "scripts/griffe_sphinx_roles.py"
replace(
    griffe,
    "artifactr's docstrings follow the Google style but refer to other objects with Sphinx roles,\n"
    "such as",
    "artifactr's and reflexr's docstrings follow the Google style but refer to other objects with\n"
    "Sphinx roles, such as",
)
sub(
    griffe,
    r"_PUBLIC_MODULES = frozenset\(\n    \{\n(?:        \"artifactr\.\w+\",\n)+    \}\n\)\n",
    "_PUBLIC_MODULES = frozenset(\n"
    '    f"{library}.{module}"\n'
    '    for library in ("artifactr", "reflexr")\n'
    "    for module in (\n"
    '        "core",\n'
    '        "telemetry",\n'
    '        "workspace",\n'
    '        "agent",\n'
    '        "scores",\n'
    '        "sql",\n'
    '        "fastapi",\n'
    '        "mcp",\n'
    '        "otel",\n'
    '        "langfuse",\n'
    '        "litellm",\n'
    '        "evals",\n'
    "    )\n"
    ")\n",
)
replace(
    griffe,
    'if target.startswith("artifactr."):',
    'if target.startswith(("artifactr.", "reflexr.")):',
)

# ─── the tools ────────────────────────────────────────────────────────────────
# The docs build is the root's: its tools are the root's docs group, and each package's goes.

DOCS_GROUP = re.compile(r'docs = \[\n(?:    "[^"\n]+",\n)+\]\n')
for name in ("artifactr", "reflexr", "evalr", "relayr"):
    path = f"packages/{name}/pyproject.toml"
    sub(path, DOCS_GROUP.pattern, "")
    replace(path, '    { include-group = "docs" },\n', "")
stackr_pyproject = "packages/stackr/pyproject.toml"
replace(
    stackr_pyproject,
    '# The documentation site (ADR-0012).\ndocs = [\n  "zensical>=0.0.66",\n'
    '  "mdx-truly-sane-lists>=1.3",\n]\n',
    "",
)
replace(stackr_pyproject, '  { include-group = "docs" },\n', "")
replace(
    "pyproject.toml",
    "\n[tool.uv]\n",
    "# The documentation site: one build over every package (docs/, mkdocs.yml).\n"
    "docs = [\n"
    '    "zensical>=0.0.66",\n'
    '    "mkdocstrings-python>=2.0.9",\n'
    '    "griffe-pydantic>=1.3.1",\n'
    '    "mdx-truly-sane-lists>=1.3",\n'
    "]\n\n[tool.uv]\n",
)
run("uv", "lock", "--quiet")

replace(
    "moon.yml",
    "  check:\n",
    """  docs:
    description: 'Build the documentation site in strict mode, and check that its lists rendered'
    script: 'uv run zensical build --strict --clean && uv run python scripts/check_site.py site'
    inputs:
      - 'mkdocs.yml'
      - 'docs/**/*'
      - 'scripts/**/*'
      - 'packages/*/src/**/*'
      - 'packages/*/CHANGELOG.md'
      - 'packages/*/schemas/**/*'
      - 'packages/stackr/**/*'
      - '*.md'
      - 'LICENSE'
      - 'uv.lock'

  docs-serve:
    description: 'Serve the documentation site with live reload at http://localhost:8000'
    command: 'uv run zensical serve'
    preset: 'server'

  check:
""",
)
replace("moon.yml", "      - 'test'\n", "      - 'test'\n      - 'docs'\n")

# ─── stackr ───────────────────────────────────────────────────────────────────
# Its site is a section of the family's, which the root builds; its reference pages are
# docs/stackr/reference/, still generated from the files they describe.

stackr = Path("packages/stackr")
replace(
    stackr / "Makefile",
    "docs: changelog ## Build the documentation site strictly, changelog included, and check its "
    "reference pages and lists, as CI does\n"
    "\t$(UV) run scripts/docs-reference --check\n"
    "\t$(UV) run zensical build --strict --clean\n"
    "\t$(UV) run python scripts/check_site.py site\n\n"
    "docs-serve: ## Serve the documentation site with live reload at http://localhost:8000\n"
    "\t$(UV) run zensical serve\n\n",
    "",
)
replace(
    stackr / "Makefile", " smoke-app docs docs-serve docs-reference ", " smoke-app docs-reference "
)
replace(
    stackr / "scripts/docs-reference",
    'PAGES = ROOT / "docs" / "reference"\n',
    "LATTICE = ROOT.parent.parent\n"
    '"""lattice\'s root, where docs/stackr/ is stackr\'s section of the site."""\n'
    'PAGES = LATTICE / "docs" / "stackr" / "reference"\n',
)
replace(
    stackr / "scripts/docs-reference",
    "path.relative_to(ROOT)}: {error}",
    "path.relative_to(LATTICE)}: {error}",
)
replace(
    stackr / "scripts/docs-reference",
    "stale.append(str(path.relative_to(ROOT)))",
    "stale.append(str(path.relative_to(LATTICE)))",
)
replace(
    stackr / "moon.yml",
    "    command: 'uv run scripts/docs-reference --check'\n",
    "    command: 'uv run scripts/docs-reference --check'\n"
    "    inputs:\n"
    "      - '**/*'\n"
    "      - '/docs/stackr/reference/**/*'\n",
)
run(
    "uv",
    "run",
    "--quiet",
    "--no-project",
    "--with",
    "pyyaml",
    "python",
    "scripts/docs-reference",
    cwd=stackr,
)
