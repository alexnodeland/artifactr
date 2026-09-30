"""The uv workspace: one environment and one lock for every package.

See stackr's RFC-0003, The uv workspace.
"""

from pathlib import Path

from lib import fail, install, locked, move, remove, replace, run

# docplan and oncall leave their libraries: in lattice they would be workspace members inside
# another member, which uv refuses.
for library, example in (("artifactr", "docplan"), ("reflexr", "oncall")):
    move(f"packages/{library}/examples/{example}", f"examples/{example}")
    Path(f"packages/{library}/examples").rmdir()

install("02-workspace")

# One lock, one .python-version and one .gitignore, at the root. The packages' .gitignore files
# were one file, apart from a line or two: evalr's is that file, and stackr keeps the lines that
# are its own.
for name in ("artifactr", "reflexr", "evalr", "stackr", "relayr"):
    remove(f"packages/{name}/uv.lock", f"packages/{name}/.python-version")
move("packages/evalr/.gitignore", ".gitignore")
for name in ("artifactr", "reflexr", "relayr"):
    remove(f"packages/{name}/.gitignore")
stackr_ignore = Path("packages/stackr/.gitignore")
own = "# stackr: the libraries' dashboards, downloaded by scripts/fetch-dashboards\n"
text = stackr_ignore.read_text()
if text.count(own) != 1:
    fail("packages/stackr/.gitignore: its own lines moved")
stackr_ignore.write_text(text[text.index(own) :])

# The quality test is the root's now, over every package, examples/ and the root's Python.
for name in ("artifactr", "reflexr", "evalr", "relayr"):
    remove(f"packages/{name}/tests/test_quality.py")

# ─── the libraries ────────────────────────────────────────────────────────────

LINT = "\n# ─── lint and format ──────────────────────────────────────────────────────────\n"
TYPES = "# ─── types ────────────────────────────────────────────────────────────────────\n"


def drop_ruff(path: str) -> None:
    """Remove a package's ruff tables, which sit between its lint and types headings."""
    text = Path(path).read_text()
    start, end = text.find(LINT), text.find(TYPES)
    if start < 0 or end < 0 or text[start:end].count("[tool.ruff]\n") != 1:
        fail(f"{path}: its ruff configuration moved")
    Path(path).write_text(text[:start] + "\n" + text[end:])


def pyright_venv(path: str) -> None:
    """Point pyright at the workspace's one environment."""
    replace(path, 'venvPath = "."\n', 'venvPath = "../.."\n')


for library, example, reason in (
    ("artifactr", "docplan", "(ADR-0044, ADR-0049)"),
    ("reflexr", "oncall", "(ADR-0020)"),
):
    path = f"packages/{library}/pyproject.toml"
    replace(
        path,
        "# evalr is not published yet: the [evals] and [langfuse] extras resolve it from GitHub, pinned\n"
        f"# {reason}.\n"
        "[tool.uv.sources]\n"
        'evalr = { git = "https://github.com/alexnodeland/evalr", rev = "7a290123aa25011b48ae9ae9cfc3e847c8cab10c" }\n',
        "# In lattice, evalr is the checkout's. A built wheel keeps the range in [project] alone.\n"
        "[tool.uv.sources]\n"
        "evalr = { workspace = true }\n",
    )
    replace(
        path,
        "# The reference implementation is a workspace member, built on the public API only.\n"
        "[tool.uv.workspace]\n"
        f'members = ["examples/{example}"]\n\n',
        "",
    )
    drop_ruff(path)
    replace(
        path,
        'include = ["src", "tests", "examples", "scripts"]\n',
        'include = ["src", "tests", "scripts"]\n',
    )
    replace(
        path,
        f'strict = ["src", "examples/{example}/src", "scripts"]\n',
        'strict = ["src", "scripts"]\n',
    )
    pyright_venv(path)
    replace(path, f'testpaths = ["tests", "examples/{example}/tests"]\n', 'testpaths = ["tests"]\n')

replace(
    "packages/artifactr/pyproject.toml",
    'source = ["src/artifactr", "examples/docplan/src/docplan"]\n',
    'source = ["src/artifactr"]\n',
)
replace(
    "packages/reflexr/pyproject.toml",
    'source = ["src/reflexr", "examples/oncall/src/oncall"]\n',
    'source = ["src/reflexr"]\n',
)

drop_ruff("packages/evalr/pyproject.toml")
pyright_venv("packages/evalr/pyproject.toml")

# relayr's distribution becomes relayr-ai, since relayr is taken on PyPI; it is still imported
# as relayr (stackr's RFC-0003, Standalone packages).
relayr = "packages/relayr/pyproject.toml"
replace(relayr, 'name = "relayr"\n', 'name = "relayr-ai"\n')
replace(relayr, 'sqlite = ["relayr[sql]", ', 'sqlite = ["relayr-ai[sql]", ')
replace(relayr, 'postgres = ["relayr[sql]", ', 'postgres = ["relayr-ai[sql]", ')
replace(
    relayr,
    "# The libraries are not on PyPI: they install from GitHub, pinned by commit, and evalr comes\n"
    "# with them at the commit their own sources pin (ADR-0012).\n"
    "[tool.uv.sources]\n"
    'artifactr-ai = { git = "https://github.com/alexnodeland/artifactr", rev = "22d3a1496a9e62012f01da68656ae089026d2a2c" }\n'
    'reflexr = { git = "https://github.com/alexnodeland/reflexr", rev = "34b9390af74e3381f089b12d7fba086fa0d2f4b3" }\n',
    "# In lattice, the libraries are the checkout's. A built wheel keeps the ranges in [project]\n"
    "# alone.\n"
    "[tool.uv.sources]\n"
    "artifactr-ai = { workspace = true }\n"
    "reflexr = { workspace = true }\n",
)
replace(
    relayr,
    '[build-system]\nrequires = ["uv_build>=0.12,<0.13"]\nbuild-backend = "uv_build"\n',
    '[build-system]\nrequires = ["uv_build>=0.12,<0.13"]\nbuild-backend = "uv_build"\n\n'
    "# Distributed as relayr-ai; imported as relayr.\n"
    "[tool.uv.build-backend]\n"
    'module-name = "relayr"\n',
)
drop_ruff(relayr)
pyright_venv(relayr)
replace("packages/relayr/src/relayr/__init__.py", 'version("relayr")', 'version("relayr-ai")')
replace("packages/relayr/tests/test_package.py", 'version("relayr")', 'version("relayr-ai")')

# The layering tests still hold the reference implementations to the public API, from their new
# place. moon's test tasks list the examples' sources as inputs, so a change there reruns them.
replace(
    "packages/artifactr/tests/test_layering.py",
    'EXAMPLE = ROOT / "examples" / "docplan" / "src" / "docplan"\n',
    'EXAMPLE = ROOT.parent.parent / "examples" / "docplan" / "src" / "docplan"\n',
)
replace(
    "packages/artifactr/tests/test_layering.py",
    'where = f"{path.relative_to(ROOT)} imports {name}, not a package\'s public name"\n',
    'where = f"{path.relative_to(EXAMPLE)} imports {name}, not a package\'s public name"\n',
)
replace(
    "packages/reflexr/tests/test_layering.py",
    'EXAMPLE = Path(__file__).parent.parent / "examples" / "oncall" / "src" / "oncall"\n',
    'EXAMPLE = Path(__file__).parents[3] / "examples" / "oncall" / "src" / "oncall"\n',
)

# docplan's tests were the only ones to run artifactr's MCP app and its lifespan. They are their
# own project now, so artifactr tests both itself, as reflexr's test_the_http_app_and_lifespan
# does.
replace(
    "packages/artifactr/tests/mcp/test_server.py",
    """async def test_building_the_server_leaves_logging_as_it_was(
""",
    """async def test_the_http_app_and_lifespan(mcp: ArtifactrMcp) -> None:
    assert mcp.http_app() is not None
    async with mcp.lifespan():
        pass


async def test_building_the_server_leaves_logging_as_it_was(
""",
)

# stackr's scripts keep their own, narrower rules, over the root's configuration.
replace(
    "packages/stackr/pyproject.toml",
    '[tool.ruff]\nline-length = 100\ntarget-version = "py312"\n',
    "[tool.ruff]\n# The root's configuration, with stackr's own rules for its scripts.\n"
    'extend = "../../pyproject.toml"\n',
)

# ─── the examples ─────────────────────────────────────────────────────────────
# Each is its own project now, with its own tests and 100% gate, under the tools' settings its
# library held for it.

EXAMPLE_TOOLS = """
# Its library's test and lint tools, which its tests ran with before.
[dependency-groups]
test = [
    "pytest>=9.1",
    "pytest-asyncio>=1.4",
    "pytest-cov>=7.1",
]
lint = ["ruff>=0.16", "pyright>=1.1.414"]
dev = [
    { include-group = "test" },
    { include-group = "lint" },
]

# ─── types ────────────────────────────────────────────────────────────────────

[tool.pyright]
include = ["src", "tests"]
strict = ["src"]
typeCheckingMode = "standard"
pythonVersion = "3.12"
venvPath = "../.."
venv = ".venv"

# ─── tests and coverage ───────────────────────────────────────────────────────

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--strict-markers", "--strict-config", "-ra"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
filterwarnings = [
    "error",
    # backoff, which Langfuse uses, calls asyncio.iscoroutinefunction, deprecated in Python 3.14.
    "ignore:'asyncio.iscoroutinefunction' is deprecated:DeprecationWarning:backoff._decorator",
]

[tool.coverage.run]
branch = true
source = ["src/{example}"]

[tool.coverage.report]
fail_under = 100
show_missing = true
skip_covered = true
exclude_also = [
    "if TYPE_CHECKING:",
    "@overload",
    "assert_never\\\\(",
    "raise NotImplementedError",
    "^\\\\s*\\\\.\\\\.\\\\.$",
    "class .*\\\\(Protocol.*\\\\):",
]
"""

for example in ("docplan", "oncall"):
    path = f"examples/{example}/pyproject.toml"
    text = Path(path).read_text()
    Path(path).write_text(text + EXAMPLE_TOOLS.replace("{example}", example))

# docplan's types were checked with artifactr's stubs for the untyped libraries (dspy among
# them), and still are.
replace(
    "examples/docplan/pyproject.toml",
    'venvPath = "../.."\nvenv = ".venv"\n',
    'venvPath = "../.."\nvenv = ".venv"\nstubPath = "../../packages/artifactr/typings"\n',
)

# docplan's [dspy] extra names evalr, which is a member too.
replace(
    "examples/docplan/pyproject.toml",
    "[tool.uv.sources]\nartifactr-ai = { workspace = true }\n",
    "[tool.uv.sources]\nartifactr-ai = { workspace = true }\nevalr = { workspace = true }\n",
)

run("uv", "lock", "--quiet")

# With one configuration, a sibling package is first-party wherever it is imported, as the
# package's own modules are, so the imports that name a sibling are sorted again, by the ruff
# the lock pins.
run("uvx", f"ruff@{locked('ruff')}", "check", "--quiet", "--select", "I", "--fix", ".")
