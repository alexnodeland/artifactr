"""stackr provisions the libraries' dashboards from the checkout.

See stackr's RFC-0003, Releases and versioning.

The libraries' dashboards sit beside stackr's in lattice, so stackr's Grafana mounts them where
they are. The dashboard archives on the libraries' releases, stackr's fetch-dashboards and its
pins in versions.env retire. The libraries still generate and test their dashboards.
"""

from pathlib import Path

from lib import remove, replace, run

for library in ("artifactr", "reflexr"):
    remove(f"packages/{library}/.github/workflows/release-assets.yml")

# artifactr's test of the release step goes with the release step.
test = "packages/artifactr/tests/test_dashboards.py"
replace(
    test,
    "import os\nimport re\nimport shutil\nimport subprocess\nimport tarfile\nimport textwrap\n",
    "import re\n",
)
replace(
    test,
    'RELEASE_ASSETS = ROOT / ".github" / "workflows" / "release-assets.yml"\n\n'
    'STACKR_ARCHIVE = "{library}-dashboards-{version}.tar.gz"\n'
    '"""The archive stackr\'s ``scripts/fetch-dashboards`` downloads from the release tagged\n'
    '``v{version}``, with the version\'s ``v`` left out."""\n',
    "",
)
text = Path(test).read_text()
start = text.index("def _script(step: str) -> str:\n")
end = text.index("def test_drift_is_caught() -> None:\n")
if "def test_the_release_attaches_the_archive_stackr_fetches(" not in text[start:end]:
    raise SystemExit(f"setup: {test}: the release test moved")
Path(test).write_text(text[:start] + text[end:])

stackr = Path("packages/stackr")
remove(str(stackr / "scripts/fetch-dashboards"), str(stackr / ".gitignore"))
replace(stackr / "pyproject.toml", '  "scripts/fetch-dashboards",\n', "")
replace(stackr / "Makefile", " logs dashboards tenant ", " logs tenant ")
replace(stackr / "Makefile", "up: .env dashboards ## ", "up: .env ## ")
replace(
    stackr / "Makefile",
    "dashboards: ## Download the libraries' Grafana dashboards pinned in versions.env\n"
    "\t$(UV) run scripts/fetch-dashboards\n\n",
    "",
)
replace(
    stackr / "versions.env",
    "\n# The libraries' Grafana dashboards, provisioned by release. scripts/fetch-dashboards\n"
    "# downloads each pinned release's dashboard archive; an empty version is skipped.\n"
    "# A *_SHA256 value, when set, must match the archive.\n"
    "ARTIFACTR_DASHBOARDS_VERSION=\n"
    "ARTIFACTR_DASHBOARDS_SHA256=\n"
    "REFLEXR_DASHBOARDS_VERSION=\n"
    "REFLEXR_DASHBOARDS_SHA256=\n",
    "",
)
replace(
    stackr / "compose.yaml",
    "      - ./deploy/grafana/dashboards:/var/lib/grafana/dashboards:ro\n",
    "      # Each directory is a folder: stackr's, and the libraries', from the checkout.\n"
    "      - ./deploy/grafana/dashboards/stackr:/var/lib/grafana/dashboards/stackr:ro\n"
    "      - ../artifactr/deploy/grafana/dashboards:/var/lib/grafana/dashboards/artifactr:ro\n"
    "      - ../reflexr/deploy/grafana/dashboards:/var/lib/grafana/dashboards/reflexr:ro\n",
)
replace(
    stackr / "deploy/grafana/provisioning/dashboards/dashboards.yaml",
    "# Dashboards from files: each directory under deploy/grafana/dashboards is a\n"
    "# folder. `stackr/` is committed; the libraries' folders are downloaded by\n"
    "# scripts/fetch-dashboards at the versions pinned in versions.env.\n",
    "# Dashboards from files: each directory under /var/lib/grafana/dashboards is a\n"
    "# folder. compose.yaml mounts stackr's, and the libraries', from lattice's\n"
    "# packages/<library>/deploy/grafana/dashboards.\n",
)

# The reference pages list the Makefile's targets and versions.env's pins.
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
