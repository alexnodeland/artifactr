"""Every package declares each module its shipped code imports.

See stackr's RFC-0003, The uv workspace. In one environment every member and dependency is
importable, so an import a package doesn't declare passes silently, and fails for someone who
installs the package alone. deptry found eight; each is declared at the lowest version that the
dependency which brought it in requires, so no install set narrows, and deptry joins check.
"""

from lib import replace, run

artifactr = "packages/artifactr/pyproject.toml"
replace(artifactr, '    "jsonpatch>=1.33",\n', '    "jsonpatch>=1.33",\n    "jsonpointer>=1.9",\n')
replace(
    artifactr,
    'litellm = [\n    "pydantic-ai-slim[openai]>=2.51",\n]\n',
    'litellm = [\n    "pydantic-ai-slim[openai]>=2.51",\n    "httpx2>=2.7",\n]\n',
)

reflexr = "packages/reflexr/pyproject.toml"
replace(
    reflexr,
    '    "pydantic-ai-slim>=2.51",\n    "pydantic-graph>=2.51",\n',
    '    "pydantic-ai-slim>=2.51",\n    "pydantic-core>=2.46.0",\n    "pydantic-graph>=2.51",\n',
)
replace(
    reflexr,
    'litellm = ["pydantic-ai-slim[openai]>=2.51"]\n',
    'litellm = ["pydantic-ai-slim[openai]>=2.51", "httpx2>=2.7"]\n',
)

# starlette comes with fastapi (0.141 requires starlette>=0.46.0) and with mcp (2.2 requires
# starlette>=0.27), and both extras import it.
for path in (artifactr, reflexr):
    replace(
        path,
        'fastapi = ["fastapi>=0.141"]\n',
        'fastapi = ["fastapi>=0.141", "starlette>=0.46.0"]\n',
    )
    replace(path, 'mcp = ["mcp>=2.2"]\n', 'mcp = ["mcp>=2.2", "starlette>=0.27"]\n')

evalr = "packages/evalr/pyproject.toml"
replace(evalr, '    "pydantic>=2.13",\n', '    "pydantic>=2.13",\n    "annotated-types>=0.6.0",\n')
replace(evalr, 'hf = ["datasets>=5.0"]\n', 'hf = ["datasets>=5.0", "huggingface-hub>=0.25.0"]\n')

replace(
    ".moon/tasks/distribution.yml",
    "  check:\n    deps:\n      - 'standalone'\n",
    "  check:\n    deps:\n      - 'standalone'\n      - 'deptry'\n",
)

run("uv", "lock", "--quiet")
