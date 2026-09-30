"""The images build from lattice's root, and one dev container replaces four.

See stackr's RFC-0003, Migration and Dev container.

docplan's and oncall's images install from the workspace's one uv.lock, so their builds start
from the root. Each has its own Dockerfile.dockerignore, beside it, which lets in the workspace's
manifests and the sources it installs.
"""

from pathlib import Path

from lib import install, move, remove, replace

install("05-builds")

for library, example in (("artifactr", "docplan"), ("reflexr", "oncall")):
    replace(
        f"packages/{library}/compose.yaml",
        f"      context: .\n      dockerfile: examples/{example}/Dockerfile\n",
        f"      # lattice's root, which holds the one uv.lock.\n"
        f"      context: ../..\n      dockerfile: examples/{example}/Dockerfile\n",
    )
    dockerfile = Path(f"examples/{example}/Dockerfile")
    replace(
        dockerfile,
        "# Build it from the repository root: `docker compose --profile app build`.\n",
        f"# Build it from lattice's root, which holds the one uv.lock: `moon run {library}:app-up`\n"
        f"# does, through {library}'s compose.yaml. Dockerfile.dockerignore, beside this file, lets\n"
        f"# in what it installs.\n",
    )

# Nothing installs from git any more, so the images need no git (artifactr ADR-0044, reflexr
# ADR-0020 and ADR-0025).
replace(
    "examples/docplan/Dockerfile",
    "# uv fetches evalr, which the [evals] extra needs, from GitHub until it is published (ADR-0044).\n"
    "RUN apt-get update \\\n"
    "    && apt-get install -y --no-install-recommends git ca-certificates \\\n"
    "    && rm -rf /var/lib/apt/lists/*\n\n",
    "",
)
replace(
    "examples/oncall/Dockerfile",
    "# uv fetches evalr, which the [langfuse] extra needs for the score mapping and ports, from GitHub\n"
    "# until it is published (ADR-0020, ADR-0025).\n"
    "RUN apt-get update \\\n"
    "    && apt-get install -y --no-install-recommends git ca-certificates \\\n"
    "    && rm -rf /var/lib/apt/lists/*\n\n",
    "",
)

# The libraries' .dockerignore files were for builds from their roots; lattice's root has one,
# for any build without its own.
move("packages/artifactr/.dockerignore", ".dockerignore")
replace(
    ".dockerignore",
    "# What docker builds from the repository root leave out.\n",
    "# What docker builds from lattice's root leave out, unless a Dockerfile has its own list.\n",
)
remove("packages/reflexr/.dockerignore")

# One dev container, at the root: the libraries' were each built on their own contributor
# stack, and stackr's drove the host's Docker.
for name in ("artifactr", "reflexr", "evalr", "stackr"):
    remove(f"packages/{name}/.devcontainer")
