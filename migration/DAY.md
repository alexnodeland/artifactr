# The day: moving into lattice

The runbook for stackr's RFC-0003, Migration, "The day", steps 0 to 7, as commands. Nothing here has been run. Run each block by hand, in order, and move on only when its "Done when" holds. Steps marked **Maintainer** need the account owner, in GitHub's settings or at the DNS host.

You need `gh`, authenticated as `alexnodeland` with the `repo`, `workflow` and `admin:repo_hook` scopes, plus git, git-filter-repo, uv, moon (`proto use` in a checkout), jq and Docker. The commands assume `REHEARSAL=~/anodeland/projects/code/lattice-rehearsal`.

## 0. Domain, and the two Apps

**Maintainer.**

- **Verify the domain.** In <https://github.com/settings/pages>, add `alexnodeland.com`, then add the TXT record GitHub shows (`_github-pages-challenge-alexnodeland.alexnodeland.com`) at the DNS host, and verify.
- **Create the release App.** Go to <https://github.com/settings/apps/new>.
  - Name it `lattice-release`, set any homepage URL, and turn the webhook off.
  - Repository permissions: Contents *Read and write*, Pull requests *Read and write*, and Metadata *Read-only*, which is always on. Nothing else.
  - "Where can this GitHub App be installed?": *Only on this account*.
  - Create it, note its **Client ID**, and generate a **private key** (a `.pem` file).
- **Renovate.** Install it after step 2, from <https://github.com/apps/renovate>, for `alexnodeland/lattice` only.

Done when: the Pages settings show `alexnodeland.com` verified, and the App exists with its Client ID and key in hand.

## 1. Freeze

Pause the loop, and merge nothing in the old repositories. Then check that the sources are the commits the rehearsal used. `import.sh` stops on any other, and a moved source is rehearsed again before the day goes on.

```sh
for r in artifactr reflexr evalr stackr; do echo "$r $(gh api repos/alexnodeland/$r/commits/main --jq .sha)"; done
echo "relayr $(gh api repos/alexnodeland/relayr/commits/chore/foundation --jq .sha)"
sed -n '/^rev_of()/,/^}/p' "$REHEARSAL/migration/import.sh"
for r in artifactr reflexr evalr stackr; do gh pr list -R alexnodeland/$r --state open; done
```

Done when: every SHA matches its pin, and no pull request is open apart from Dependabot's, which stay unmerged (Renovate replaces them in lattice).

## 2. Import

```sh
cd "$REHEARSAL"
migration/lattice.sh ~/anodeland/projects/code/lattice-day   # an empty directory
cd ~/anodeland/projects/code/lattice-day/lattice
```

Check it as rehearsed:

```sh
uv sync --locked --all-packages --all-groups --all-extras
docker run -d --rm --name lattice-day-pg -e POSTGRES_PASSWORD=lattice -p 127.0.0.1:54341:5432 postgres:17
until docker exec lattice-day-pg pg_isready -q -U postgres; do sleep 1; done
docker exec lattice-day-pg psql -U postgres -c 'CREATE DATABASE artifactr' -c 'CREATE DATABASE reflexr'
ARTIFACTR_TEST_POSTGRES_URL=postgresql+asyncpg://postgres:lattice@localhost:54341/artifactr \
REFLEXR_TEST_POSTGRES_URL=postgresql+asyncpg://postgres:lattice@localhost:54341/reflexr \
  moon run :check
docker stop lattice-day-pg
```

The rewritten messages carry 18 closing keywords that point at the old repositories, such as `Closes alexnodeland/artifactr#63`. When `main` is pushed, none may point at an issue that is still open. On 2026-09-30 none did. Check again:

```sh
for r in artifactr reflexr evalr stackr relayr; do
  gh api "repos/alexnodeland/$r/issues?state=open&per_page=100" \
    --jq ".[] | select(.pull_request == null) | \"$r#\(.number)\""
done | sort > /tmp/open.txt
git log --format=%B \
  | grep -ioE '\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b:? +alexnodeland/[a-z]+#[0-9]+' \
  | sed -E 's/.*alexnodeland\///I' | sort -u > /tmp/closing.txt
comm -12 /tmp/open.txt /tmp/closing.txt   # must print nothing
```

Create the repository with Actions off, so the first push runs nothing before the settings, secrets and Pages exist. Then push `main` and the one tag.

```sh
gh repo create alexnodeland/lattice --public \
  --description "The family's packages: artifactr, reflexr, evalr, relayr and stackr." \
  --homepage https://lattice.alexnodeland.com --disable-wiki
gh api -X PUT repos/alexnodeland/lattice/actions/permissions -F enabled=false
git remote add origin https://github.com/alexnodeland/lattice.git
git push origin main
git push origin artifactr-v0.1.0
```

Pushing the history adds a "mentioned in a commit" entry to each issue and pull request in the old repositories that a message names. That is expected, and it closes nothing (the check above).

**`artifactr-v0.1.0` needs no GitHub Release in lattice.** release-please finds a package's last release by its tag when there is no Release object (release-please 17, `backfillReleasesFromTags`). The 0.1.0 release and its notes stay in `alexnodeland/artifactr`.

Done when: these three agree, and the tags list shows `artifactr-v0.1.0`.

```sh
git rev-parse HEAD
gh api repos/alexnodeland/lattice/commits/main --jq .sha
gh api repos/alexnodeland/lattice/tags --jq '.[].name'
```

## 3. Settings

Merges are squash-only, with the pull request's title and body.

```sh
gh api -X PATCH repos/alexnodeland/lattice \
  -F allow_squash_merge=true -F allow_merge_commit=false -F allow_rebase_merge=false \
  -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY \
  -F delete_branch_on_merge=true -F allow_update_branch=true -F has_wiki=false
```

Secret scanning with push protection, and private vulnerability reporting:

```sh
gh api -X PATCH repos/alexnodeland/lattice --input - <<'JSON'
{"security_and_analysis": {"secret_scanning": {"status": "enabled"},
                           "secret_scanning_push_protection": {"status": "enabled"}}}
JSON
gh api -X PUT repos/alexnodeland/lattice/private-vulnerability-reporting
```

The ruleset is the siblings' `main` ruleset (deletion, non-fast-forward, squash-only pull requests, linear history), plus the two required checks, `CI` and `Title`, from GitHub Actions (app 15368), on branches up to date with `main`:

```sh
gh api -X POST repos/alexnodeland/lattice/rulesets --input - <<'JSON'
{
  "name": "main",
  "target": "branch",
  "enforcement": "active",
  "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
  "bypass_actors": [],
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "required_linear_history"},
    {"type": "pull_request", "parameters": {
      "allowed_merge_methods": ["squash"],
      "dismiss_stale_reviews_on_push": false,
      "require_code_owner_review": false,
      "require_last_push_approval": false,
      "required_approving_review_count": 0,
      "required_review_thread_resolution": false}},
    {"type": "required_status_checks", "parameters": {
      "strict_required_status_checks_policy": true,
      "required_status_checks": [
        {"context": "CI", "integration_id": 15368},
        {"context": "Title", "integration_id": 15368}]}}
  ]
}
JSON
```

The labels the transferred issues carry, beyond GitHub's defaults. release-please creates its own.

```sh
gh label create decision --color D93F0B --description "Needs a maintainer decision" -R alexnodeland/lattice
gh label create roadmap --color 0E8A16 --description "Planned work after the current RFC" -R alexnodeland/lattice
gh label create tracking --color 5319E7 --description "Tracks an RFC or a multi-PR effort" -R alexnodeland/lattice
```

**Maintainer:**

- Install the `lattice-release` App on `alexnodeland/lattice` only. Also install Renovate (step 0).
- Set the App's secrets:

  ```sh
  gh secret set RELEASE_APP_CLIENT_ID -R alexnodeland/lattice --body "<the App's Client ID>"
  gh secret set RELEASE_APP_PRIVATE_KEY -R alexnodeland/lattice < lattice-release.private-key.pem
  ```

Then turn Actions on, with read-only default permissions (each workflow grants its own):

```sh
gh api -X PUT repos/alexnodeland/lattice/actions/permissions -F enabled=true -f allowed_actions=all
gh api -X PUT repos/alexnodeland/lattice/actions/permissions/workflow \
  -f default_workflow_permissions=read -F can_approve_pull_request_reviews=false
```

Done when: a direct push is refused.

```sh
git commit --allow-empty -m "chore: test the ruleset"
git push origin HEAD:main    # must be refused
git reset --hard HEAD~1
```

## 4. Pages

```sh
gh api -X POST repos/alexnodeland/lattice/pages -f build_type=workflow
gh api -X PUT repos/alexnodeland/lattice/pages -f build_type=workflow -f cname=lattice.alexnodeland.com
```

**Maintainer:** add the DNS record `lattice CNAME alexnodeland.github.io`.

Deploy, and once the certificate is issued, enforce HTTPS:

```sh
gh workflow run docs.yml -R alexnodeland/lattice
gh run watch -R alexnodeland/lattice "$(gh run list -R alexnodeland/lattice --workflow docs.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
gh api repos/alexnodeland/lattice/pages --jq '.https_certificate.state'   # approved
gh api -X PUT repos/alexnodeland/lattice/pages -F https_enforced=true
```

Done when: `curl -sI https://lattice.alexnodeland.com | head -1` shows 200.

## 5. Verify

Open a trivial pull request through the ruleset. Here it opens the RFC's amendments (`migration/rfc-0003-amendments.md`), which are due first anyway.

```sh
git switch -c docs/rfc-0003-amendments
# apply migration/rfc-0003-amendments.md to docs/stackr/rfcs/0003-one-repository-lattice.md
git commit -am "docs(rfc): RFC-0003's amendments from the rehearsal"
git push -u origin docs/rfc-0003-amendments
gh pr create -R alexnodeland/lattice --fill
gh pr checks --watch
gh pr merge --squash --delete-branch
```

After the merge, release.yml runs on `main` for the first time, as the App. Every commit since the import is `build:`, `style:`, `docs:` or `ci:`, none of which releases, so release-please opens no release pull request yet. Check that the run minted its token and succeeded:

```sh
gh run watch -R alexnodeland/lattice "$(gh run list -R alexnodeland/lattice --workflow release.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
```

The first `feat:` or `fix:` merged after the day opens the first release pull request. Check then that CI and Title run on it; if they don't, the App's token isn't reaching release-please.

Done when: CI and Title are green on the pull request, release.yml's run succeeded, and the site has every section.

## 6. Issues

Transfer the 12 open issues. Old URLs redirect. Then rewrite each one's bare `#N`, in its body and its comments, with the import's two rules for its old repository.

```sh
cd "$REHEARSAL/migration"
for pair in artifactr:62 artifactr:54 artifactr:23 reflexr:72 reflexr:53 reflexr:21 \
            stackr:7 stackr:6 stackr:5 stackr:4 stackr:3 stackr:2; do
  repo=${pair%%:*}; number=${pair#*:}
  url=$(gh issue transfer "$number" alexnodeland/lattice -R "alexnodeland/$repo")
  new=${url##*/}
  echo "$repo#$number -> lattice#$new"
  rewrite() {  # stdin: text; stdout: text with the messages/<repo>.txt rules applied
    python3 -c '
import re, sys
rules = [line.removeprefix("regex:").split("==>") for line in open(sys.argv[1]).read().splitlines()]
text = sys.stdin.read()
for pattern, replacement in rules:
    text = re.sub(pattern, replacement, text)
sys.stdout.write(text)' "messages/$repo.txt"
  }
  body=$(gh api "repos/alexnodeland/lattice/issues/$new" --jq '.body // ""')
  gh api -X PATCH "repos/alexnodeland/lattice/issues/$new" -f body="$(printf '%s' "$body" | rewrite)" > /dev/null
  gh api "repos/alexnodeland/lattice/issues/$new/comments" --paginate --jq '.[] | @base64' |
    while read -r comment; do
      id=$(printf '%s' "$comment" | base64 -d | jq -r .id)
      text=$(printf '%s' "$comment" | base64 -d | jq -r .body)
      gh api -X PATCH "repos/alexnodeland/lattice/issues/comments/$id" \
        -f body="$(printf '%s' "$text" | rewrite)" > /dev/null
    done
done
```

Done when: each old issue URL lands in lattice, `gh issue list -R alexnodeland/lattice` shows 12, and no body or comment holds a bare `#N` that meant the old repository.

## 7. Resume

- Update the links that still name the old repositories, in a pull request:
  - stackr's docs;
  - `[project.urls]` in each package's `pyproject.toml`: Homepage and Documentation become `https://lattice.alexnodeland.com/<package>/`; Repository becomes `https://github.com/alexnodeland/lattice`; Issues becomes `https://github.com/alexnodeland/lattice/issues`; Changelog becomes `https://github.com/alexnodeland/lattice/blob/main/packages/<package>/CHANGELOG.md`.
  - The READMEs' links became absolute in the setup commits, so they need nothing here.
- Restart the loop against lattice.
- **Maintainer, phase 7:** the Claude token secret, `gh secret set CLAUDE_CODE_OAUTH_TOKEN -R alexnodeland/lattice`, and the Codespaces prebuilds, in the repository's Codespaces settings.

Done when: new work opens against lattice.
