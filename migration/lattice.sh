#!/usr/bin/env bash
# The migration into lattice (stackr's RFC-0003), from fresh clones to the finished tree, in one
# run: the import (import.sh), then one commit per setup step.
#
# Usage: migration/lattice.sh WORK_DIR
#
# WORK_DIR must be empty or absent. The result is WORK_DIR/lattice, on main, with the tags.
#
# import.sh makes the first commits: an empty root and one merge per repository. Each setup step
# after them is setup/NN-name.py, which changes the checkout (with the prepared files in
# files/NN-name/), and setup/NN-name.txt, its commit message. LATTICE_DATE, when set, is the
# date of every commit the run creates, so that two runs give the same commits.
#
# Needs git, git-filter-repo, uv, and network access to GitHub and PyPI.
set -euo pipefail

MIGRATION=$(cd "$(dirname "$0")" && pwd)
WORK=${1:?usage: lattice.sh WORK_DIR}

"$MIGRATION/import.sh" "$WORK"
WORK=$(cd "$WORK" && pwd)
export LATTICE_WORK=$WORK
export PYTHONDONTWRITEBYTECODE=1 # nothing written into migration/
cd "$WORK/lattice"

for step in "$MIGRATION"/setup/[0-9][0-9]-*.py; do
  name=$(basename "$step" .py)
  echo "==> $name"
  PYTHONPATH=$MIGRATION uv run --quiet --no-project --with pyyaml python "$step"
  git add --all
  if [[ -n ${LATTICE_DATE:-} ]]; then
    GIT_AUTHOR_DATE=$LATTICE_DATE GIT_COMMITTER_DATE=$LATTICE_DATE \
      git commit --quiet --file "$MIGRATION/setup/$name.txt"
  else
    git commit --quiet --file "$MIGRATION/setup/$name.txt"
  fi
done

echo "==> lattice: $(git rev-list --count HEAD) commits, $(git tag | wc -l | tr -d ' ') tag(s)"
git log --oneline --first-parent -n 20
