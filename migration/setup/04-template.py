"""stackr's template, rendered from lattice's root.

See stackr's RFC-0003, stackr's template from inside lattice.

Copier reads copier.yml at a repository's root. From packages/stackr it would see a directory
that isn't a repository's root, with no VCS, so everything that renders the template renders it
from the root, through the root's copier.yml.
"""

from pathlib import Path

from lib import install, replace

install("04-template")

stackr = Path("packages/stackr")
replace(
    stackr / "copier.yml",
    "#   uvx copier copy gh:alexnodeland/stackr my-app     # from GitHub\n"
    "#   uvx copier copy path/to/stackr my-app             # from a clone\n",
    "#   uvx copier copy gh:alexnodeland/lattice my-app    # from GitHub\n"
    "#   uvx copier copy path/to/lattice my-app            # from a clone\n",
)
replace(
    stackr / "copier.yml",
    "# Copier takes the latest release tag. stackr has none yet, so Copier warns that it found no\n"
    "# tags and takes HEAD instead: main's, from GitHub. `--vcs-ref` names another revision.\n"
    "#\n"
    "# The template's files are in template/. Copier takes a repository, not a directory of one,\n"
    "# so these questions live at the repository's root and point it there.\n",
    "# Copier takes the latest tag that parses as a version. lattice's tags carry their package's\n"
    "# name (stackr-v0.1.0), and none parses, so Copier warns that it found no release and takes\n"
    "# HEAD instead: main's, from GitHub. `--vcs-ref` names another revision.\n"
    "#\n"
    "# The template's files are in template/. Copier takes a repository, not a directory of one,\n"
    "# so lattice's root copier.yml includes these questions and points Copier at template/.\n",
)

replace(
    stackr / "scripts/check-template",
    "ROOT = Path(__file__).resolve().parent.parent\n",
    "ROOT = Path(__file__).resolve().parent.parent\n"
    "LATTICE = ROOT.parent.parent\n"
    '"""lattice\'s root, whose copier.yml points Copier at the template."""\n',
)
replace(
    stackr / "scripts/check-template", "            str(ROOT),\n", "            str(LATTICE),\n"
)
replace(
    stackr / "scripts/smoke",
    '--data libraries=both --data evals=true . "$app_dir" 2>/dev/null ||',
    '--data libraries=both --data evals=true ../.. "$app_dir" 2>/dev/null ||',
)

# CI's Template and Smoke jobs run these, with their matrix values in the environment.
replace(
    stackr / "moon.yml",
    "      - 'validate'\n      - 'reference'\n",
    """      - 'validate'
      - 'reference'

  # CI's Template and Smoke jobs, with their matrix values in the environment.
  template:
    description: 'Generate one application from the template and run its own checks'
    command: 'scripts/check-app'
    inputs:
      - '**/*'
      - '/copier.yml'
      - '$TEMPLATE_LIBRARIES'
      - '$TEMPLATE_EVALS'
      - '$TEMPLATE_PYTHON'
    options:
      cache: false

  smoke:
    description: 'Start the stack (PROFILES, STACKR_DATABASE) and send telemetry through it'
    script: 'make up && make smoke'
    options:
      cache: false

  smoke-app:
    description: 'Run an application from the template beside the running stack'
    command: 'make smoke-app'
    options:
      cache: false
""",
)
