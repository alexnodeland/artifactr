#!/usr/bin/env bash
# The import (stackr's RFC-0003, Migration): each repository's history, rewritten into
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

# The sources, pinned at the commits rehearsed: each established repository's main, and relayr's
# unmerged foundation. The prepared files and the setup steps' edits were written against these
# trees, so a source that has moved stops the run: rehearse again, then move its pin.
# grantr and portalr aren't imported: each holds one initial commit with a README and a license.
PACKAGES="artifactr reflexr evalr stackr relayr"

branch_of() { if [[ $1 == relayr ]]; then echo chore/foundation; else echo main; fi; }
rev_of() {
  case $1 in
    artifactr) echo 6eca8e013924617f7e4960574b5037fe8aa0bf37 ;;
    reflexr) echo d11aecec76f7a387ffa9610c7297fef03dd2ba0d ;;
    evalr) echo 7a290123aa25011b48ae9ae9cfc3e847c8cab10c ;;
    stackr) echo 455a31c1f0cffdd5f0e5240e9086c3e0ae89ef8a ;;
    relayr) echo fd54088426b8427aad1d3bb3721a69e1bdb743e2 ;;
  esac
}

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
  tip=$(git -C "$clone" rev-parse HEAD)
  if [[ $tip != "$(rev_of "$name")" ]]; then
    echo "import: $name's $branch is at $tip, not the rehearsed $(rev_of "$name")" >&2
    exit 1
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
