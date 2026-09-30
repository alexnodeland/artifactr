#!/usr/bin/env bash
# The import (stackr RFC-0003, Migration): each repository's history, rewritten into
# packages/<name>/ in a fresh clone, then merged into a new lattice repository as unrelated
# histories, one after another.
#
# Usage: migration/import.sh WORK_DIR
#
# Writes WORK_DIR/clones/<name> (the rewritten clones), WORK_DIR/out/commit-map/<name>
# (filter-repo's map from old commit to new, for the changelogs and for applications whose
# `_commit` names an old stackr commit) and WORK_DIR/lattice (the new repository, on main).
#
# LATTICE_DATE, when set, is the date of every commit this script creates, so that two runs give
# the same commits. The imported commits keep their own dates either way.
set -euo pipefail

MIGRATION=$(cd "$(dirname "$0")" && pwd)
WORK=${1:?usage: import.sh WORK_DIR}
GITHUB=${LATTICE_SOURCE:-https://github.com/alexnodeland}

# The sources: the established repositories' main, and relayr's unmerged foundation, pinned.
# grantr and portalr aren't imported: each holds one initial commit with a README and a license.
PACKAGES="artifactr reflexr evalr stackr relayr"
RELAYR_BRANCH=chore/foundation
RELAYR_REV=fd54088426b8427aad1d3bb3721a69e1bdb743e2

branch_of() { if [[ $1 == relayr ]]; then echo "$RELAYR_BRANCH"; else echo main; fi; }

if [[ -e $WORK/clones || -e $WORK/lattice ]]; then
  echo "import: $WORK already holds clones or lattice; start from an empty directory" >&2
  exit 1
fi
mkdir -p "$WORK/clones" "$WORK/out/commit-map"
WORK=$(cd "$WORK" && pwd)

commit_env() {
  if [[ -n ${LATTICE_DATE:-} ]]; then
    GIT_AUTHOR_DATE=$LATTICE_DATE GIT_COMMITTER_DATE=$LATTICE_DATE "$@"
  else
    "$@"
  fi
}

for name in $PACKAGES; do
  clone=$WORK/clones/$name
  branch=$(branch_of "$name")
  echo "==> $name: cloning $branch"
  git clone --quiet --single-branch --branch "$branch" "$GITHUB/$name.git" "$clone"
  if [[ $name == relayr ]]; then
    tip=$(git -C "$clone" rev-parse HEAD)
    if [[ $tip != "$RELAYR_REV" ]]; then
      echo "import: relayr's $RELAYR_BRANCH is at $tip, not the rehearsed $RELAYR_REV" >&2
      exit 1
    fi
  fi
  echo "    $name: $(git -C "$clone" rev-parse HEAD), $(git -C "$clone" rev-list --count HEAD) commits"

  # The message rules are the RFC's two, in order, except that the first starts with
  # (?<![\w/]) where the RFC has \b: artifactr's aa3534a and reflexr's bc12afe already say
  # "Refs alexnodeland/evalr#17", which \b would rewrite a second time.
  git -C "$clone" filter-repo --quiet \
    --to-subdirectory-filter "packages/$name" \
    --tag-rename '':"$name-" \
    --replace-message "$MIGRATION/messages/$name.txt" >/dev/null 2>&1
  cp "$clone/.git/filter-repo/commit-map" "$WORK/out/commit-map/$name"
done

echo "==> lattice"
lattice=$WORK/lattice
git init --quiet --initial-branch=main "$lattice"
commit_env git -C "$lattice" commit --quiet --allow-empty -F - <<'MSG'
chore: start lattice, the family's one repository

lattice holds the family's packages, each with its history (stackr's RFC-0003). This empty
commit is the root that each repository's history is merged into.
MSG

for name in $PACKAGES; do
  clone=$WORK/clones/$name
  branch=$(branch_of "$name")
  source=$(git -C "$clone" rev-parse HEAD)
  git -C "$lattice" fetch --quiet --no-tags "$clone" \
    "+refs/heads/$branch:refs/import/$name" "+refs/tags/*:refs/tags/*"
  old=$(awk -v new="$source" '$2 == new { print $1 }' "$WORK/out/commit-map/$name")
  # git merge reads a message from a file, never from standard input.
  cat >"$WORK/out/message" <<MSG
chore: import $name, with its history, into packages/$name

The history of $name's $branch, at commit
$old,
rewritten by git filter-repo:

- every path moves under packages/$name/;
- each tag gains the prefix $name-, as artifactr's v0.1.0 becomes artifactr-v0.1.0;
- each reference in a message to an issue or pull request names its repository, so a bare #N
  becomes alexnodeland/$name#N, and a mention such as "reflexr #N" becomes
  alexnodeland/reflexr#N.
MSG
  commit_env git -C "$lattice" merge --quiet --no-ff --allow-unrelated-histories \
    -F "$WORK/out/message" "refs/import/$name"
  git -C "$lattice" update-ref -d "refs/import/$name"
done

echo "==> imported: $(git -C "$lattice" rev-list --count HEAD) commits, tags: $(git -C "$lattice" tag | tr '\n' ' ')"
