# RFC-0003: what the rehearsal settled, in full

stackr's RFC-0003, "One repository: lattice", is Accepted. Its phase 1 rehearsal found text that is wrong, or that the rehearsal had to settle. Each entry below quotes the RFC as it stands and gives what lattice does instead, with the evidence.

The RFC process changes an Accepted RFC's design sections only through a superseding RFC, so these were never applied to it. lattice#2 lists them in RFC-0003's Tracking section, one line each. This file is the source for phase 3's ADRs, which record each decision in full.

## 1. The first message rule rewrites a reference twice

**Migration, History.** Now:

> The message rules, in order: `regex:\b(artifactr|reflexr|evalr|stackr|relayr) ?#(\d+)==>alexnodeland/\1#\2`, then `regex:(?<![\w/])#(\d+)==>alexnodeland/<repo>#\1`. The first catches prose such as "reflexr #90" or "reflexr#90"; the second catches every bare reference, such as `Closes #63` and `(#64)`. About 41 bare references sit in the commit bodies, beyond the squash titles' `(#N)`.

Replace with:

> The message rules, in order: `regex:(?<![\w/])(artifactr|reflexr|evalr|stackr|relayr) ?#(\d+)==>alexnodeland/\1#\2`, then `regex:(?<![\w/])#(\d+)==>alexnodeland/<repo>#\1`. The first catches prose such as "reflexr #90" or "reflexr#90", and leaves a reference that already names its owner alone; the second catches every bare reference, such as `Closes #63` and `(#64)`. The four histories hold 240 bare references: 192 in the squash titles' `(#N)`, and 48 in the bodies, 15 of them prose.

Why: artifactr's aa3534a and reflexr's bc12afe already say `Refs alexnodeland/evalr#17`, which `\b` matches after the slash and turns into `alexnodeland/alexnodeland/evalr#17`.

## 2. The import pins every source

**Migration, History.** Now:

> **History,** for artifactr, reflexr, evalr and stackr, and for relayr's `chore/foundation` branch (fd54088), each in a fresh clone:

Replace with:

> **History,** for artifactr, reflexr, evalr and stackr at their rehearsed `main`, and for relayr's `chore/foundation` branch, each at the commit the rehearsal used and in a fresh clone. The setup steps' edits and prepared files were written against those trees, so a source that has moved stops the run, and is rehearsed again first:

## 3. The setup is a series of commits

**Migration.** Now:

> - **The setup commit** moves the docs, docplan and oncall; changes sibling sources to `{ workspace = true }`; replaces the per-repository lockfiles, workflows, hooks, tool configuration, quality tests, dev containers and project pages with the root's; generates the changelogs' history; points docplan's and oncall's images at the root context; and retires the dashboard releases.

Replace with:

> - **The setup** is a series of commits after the import, one concern each, since the import is pushed directly and each commit must read on its own: the uv workspace; a `style:` commit that only sorts the imports that name a sibling, which `.git-blame-ignore-revs` names; moon; the declared imports deptry found; the template rendered from the root; the images and the dev container; the dashboards from the checkout; the docs; the changelogs' history; and the workflows, hooks and repository files. Together they move the docs, docplan and oncall; change sibling sources to `{ workspace = true }`; replace the per-repository lockfiles, workflows, hooks, tool configuration, quality tests, dev containers and project pages with the root's; generate the changelogs' history; point docplan's and oncall's images at the root context; and retire the dashboard releases. One test is added: artifactr's MCP app and its lifespan were covered only by docplan's tests, which leave artifactr's session.

## 4. One resolution, and what it costs

**The uv workspace.** Now:

> | Third-party versions | Resolved per repository | One resolution, so the packages must agree on every range. They agree today |

Replace with:

> | Third-party versions | Resolved per repository | One resolution, so the packages must agree on every range. They resolve together today at one cost: every litellm after 1.83.0 pins `openai<3`, which pydantic-ai-slim[openai] (`openai>=3.19`) can't share, so evalr's DSPy runs on litellm 1.83.0. Its 13 advisories are all in litellm's proxy server, which lattice never runs, and `osv-scanner.toml` records each |

## 5. The declared imports

**The uv workspace.** After the deptry paragraph, add:

> The setup declares the eight imports deptry finds there today, each at the lowest version that the dependency which brought it in requires, so no install set narrows: jsonpointer in artifactr, pydantic-core in reflexr, annotated-types and huggingface-hub in evalr, and starlette and httpx2 in artifactr's and reflexr's extras. deptry is part of each package's `check` from then on.

## 6. build writes each wheel into its own project

**Standalone packages.** Now:

> - `build` runs `uv build --package <name> --no-sources`, with `dist/**` as its outputs, so each wheel is built once.

Replace with:

> - `build` runs `uv build --no-sources --out-dir dist` from the package's directory, so its wheel lands in the project's `dist/`, which is its output; `--package` from the root would write every wheel to the root's `dist/`.

Note, not a change: `standalone` depends on `^:build`, the direct dependencies' builds, while `scripts/standalone.py` installs siblings transitively. Today every sibling a package installs is a direct dependency, or one it requests with no extras that need another.

## 7. The Bun root waits for portalr's TypeScript

**The Bun workspace, moon, CI and tooling, Phases.** Now:

> | `.moon/toolchains.yml` | `javascript` (`packageManager: bun`), `bun` and `typescript`, with `installDependencies: false` and the settings that rewrite files turned off. No Python toolchain (D3) |

Replace with:

> | `.moon/toolchains.yml` | Absent until portalr's TypeScript arrives with the portal RFC, which brings `package.json`, `bun.lock`, `biome.json`, `tsconfig.base.json`, and the `javascript`, `bun` and `typescript` toolchains. No Python toolchain (D3) |

And in `ci.yml`'s row and phase 1's exit criteria, drop `bun install --frozen-lockfile` until then.

## 8. proto leaves Python to uv

**moon.** Now:

> | `.prototools` | The versions of moon, uv and Bun, which CI installs through `moonrepo/setup-toolchain` and Renovate's `proto` manager updates |

Replace with:

> | `.prototools` | The versions of moon and uv (and Bun, with portalr), which CI installs through `moonrepo/setup-toolchain` and Renovate's `proto` manager updates, and `detect-strategy = "only-prototools"`, so proto doesn't also install Python from `.python-version`: uv owns Python |

## 9. docplan depends on evalr too

**moon.** Now:

> | docplan, oncall | artifactr, reflexr respectively |

Replace with:

> | docplan | artifactr, and evalr, which its `[dspy]` extra names |
> | oncall | reflexr |

## 10. `moon ci --downstream deep` doesn't reach dependents

**moon.** Now:

> artifactr's and reflexr's `api` tasks also depend on docplan's and oncall's `image` tasks, since their collections run against those apps. A change to either app then reaches them through `--downstream deep`, which CI uses because `moon ci` defaults to direct dependents only.

Replace with:

> artifactr's and reflexr's `api` tasks also depend on docplan's and oncall's `image` tasks, since their collections run against those apps. `moon ci --downstream deep` follows the task graph, so it reaches a dependent's task only through that task's own dependencies: an evalr-only change would run evalr's checks alone (moon 2.5.6, verified). And `moon query projects --affected` sees only a project's own files, so a change to `uv.lock` alone affects no package. CI's `scripts/affected.py` takes the projects a change touches by their files (`moon query projects --affected`) or by their tasks' inputs, which include the lock and the root's configuration (`moon query tasks --affected`), adds every project that depends on one, all the way down, from the project graph, and `moon run`s the task in each that has it.

**CI and tooling.** Now:

> | Pull requests | `moon ci --downstream deep`. Python 3.13 and 3.14 run on every pull request, since a public repository's minutes are free |

Replace with:

> | Pull requests | Check, Tests and Images run their task in every affected project and every dependent (`scripts/affected.py`). Python 3.13 and 3.14 run on every pull request, since a public repository's minutes are free |

## 11. CI on pull requests; main is nightly's; Title is its own check

**CI and tooling.** Now:

> | Keeping `main` green | One required check, `CI` (`re-actors/alls-green`, at v1.3.0 or later), and branches up to date with `main`, both in the ruleset. alls-green counts a skipped job as a failure, so jobs that run only on pull requests go in its `allowed-skips`. No merge queue, since GitHub offers it only to organizations, and `alexnodeland` is a personal account |

Replace with:

> | Keeping `main` green | Two required checks, `CI` (`re-actors/alls-green`, at v1.3.0 or later) and `Title`, and branches up to date with `main`, all in the ruleset. CI runs on pull requests only, so every job runs and none needs an `allowed-skips`. Title is a workflow of its own because CI's jobs never rerun when a title is edited. No merge queue, since GitHub offers it only to organizations, and `alexnodeland` is a personal account |

Now:

> | `main` and nightly | Every project's `check`, osv-scanner (through `google/osv-scanner-action`) over `uv.lock` and `bun.lock`, and a lychee link check |

Replace with:

> | `main` and nightly | `nightly.yml`, on every push to `main` and every night: every project's `check`, the reference implementations' images, osv-scanner (through `google/osv-scanner-action`) over `uv.lock`, with `osv-scanner.toml` beside it recording the advisories that don't apply, and a lychee link check |

Now:

> | Pull request titles | A lint against the Conventional Commits types and the module scopes, which stay as they are (`mcp`, `scores`, `template`); paths route commits to packages |

Replace with:

> | Pull request titles | `title.yml`: a lint against the Conventional Commits types, rerun whenever the title is edited. Scopes stay as they are (`mcp`, `scores`, `template`) and aren't listed, since the history has 33 and a new module brings a new scope; paths route commits to packages |

The workflows table, now:

> | `ci.yml` | **Check** (Python 3.12): `uv sync --locked --all-packages --all-groups --all-extras`, `bun install --frozen-lockfile`, and `moon ci --downstream deep :check`, with a PostgreSQL 17 service holding one database per library. **Tests** (Python 3.13, 3.14): `moon ci --downstream deep :test`. **Template** and **Smoke**: `moon ci stackr:template` and `moon ci stackr:smoke`, with the matrix values in the environment, which do nothing unless stackr is affected. **Acceptance**: starts docplan, oncall and the console service, then runs `moon ci --downstream deep :api :bdd` and Schemathesis. On pull requests only: **Title**, **Dependency review** and **OSV** (osv-scanner's pull request workflow). **CI**, the one required check |
> | `docs.yml` | The family's "one docs build": it builds on every pull request, every push to `main` and by hand, with the concurrency group `docs-${{ github.ref }}` cancelling only on pull requests, and deploys only from `main` |
> | `nightly.yml` | On pushes to `main` and nightly: every project's `check`, osv-scanner and lychee |
> | `release.yml` | release-please, the builds and their attestations |

Replace with:

> | `ci.yml` | On pull requests. **Check** (Python 3.12): `uv sync --locked --all-packages --all-groups --all-extras`, then `check` in every affected project and its dependents (`scripts/affected.py`), with a PostgreSQL 17 service holding one database per library. **Tests** (Python 3.13, 3.14): `test`, the same way. **Images**: docplan's and oncall's `image` tasks, the same way, which build each image from the root and start it on PostgreSQL. **Template** and **Smoke**: `moon ci stackr:template` and `moon ci stackr:smoke`, with the matrix values in the environment, which do nothing unless stackr's own inputs change: the template pins the libraries by revision until phase 4. **Acceptance**: starts docplan, oncall and the console service, then runs `:api :bdd` and Schemathesis. **Dependency review** and **OSV** (osv-scanner's pull request workflow). **CI**, the last job |
> | `title.yml` | **Title**, on `opened`, `edited`, `synchronize` and `reopened` |
> | `docs.yml` | The family's "one docs build", deployed from `main` on every push and by hand, in order (one concurrency group, never cancelled). CI builds the site strictly on every pull request, as the root project's `docs` task |
> | `nightly.yml` | On pushes to `main` and nightly: every project's `check`, the images, osv-scanner and lychee |
> | `release.yml` | release-please, acting as the release GitHub App with a token minted per run (`actions/create-github-app-token`, from the `RELEASE_APP_CLIENT_ID` and `RELEASE_APP_PRIVATE_KEY` secrets), so its pull request's required checks run; then the builds and their attestations |

## 12. Renovate moves the hooks too

**CI and tooling.** In the Dependencies row, now:

> its built-in `proto` manager for `.prototools` (a custom manager isn't needed),

Replace with:

> its built-in `proto` manager for `.prototools` (a custom manager isn't needed), its `pre-commit` manager, which is off by default, for the hooks' revisions,

## 13. prek and the template's own hooks

**CI and tooling.** Now:

> | Hooks | prek replaces pre-commit, with the same `.pre-commit-config.yaml` |

Replace with:

> | Hooks | prek replaces pre-commit, with the same `.pre-commit-config.yaml`, and a `.prekignore` that leaves out `packages/stackr/template/`, whose hook configuration is the generated applications' and which prek's workspace mode would otherwise run as a project of its own |

## 14. awesome-nav is enabled by listing it

**Docs.** Now:

> Zensical implements awesome-nav natively, so each folder's `.nav.yml` sets its section's order.

Replace with:

> Zensical implements awesome-nav natively once `awesome-nav` is listed under `plugins` in `mkdocs.yml`, and each folder's `.nav.yml` then sets its section's order; without it the nav is alphabetical.

## 15. The READMEs' links are absolute

**Docs.** After "Each package keeps its changelog page, included from `packages/<name>/CHANGELOG.md`.", add:

> A package's README is also its PyPI page, so its links are absolute: the site's pages, the banners from `raw.githubusercontent.com`, and the repository's files on GitHub.

**The day, step 7.** Now:

> | 7. Resume | Update the links (READMEs, stackr's docs, the packages' `pyproject.toml` URLs), and restart the loop in lattice | New work opens against lattice |

Replace with:

> | 7. Resume | Update the links (stackr's docs, the packages' `pyproject.toml` URLs), and restart the loop in lattice | New work opens against lattice |

## 16. The images' build context

**Migration.** Now:

> Each image has its own `Dockerfile.dockerignore`, which lets in the members' `pyproject.toml` files, `uv.lock` and the sources it installs.

Replace with:

> Each image has its own `Dockerfile.dockerignore`, which lets in the root's and every member's `pyproject.toml`, which `uv sync --locked` checks the lock against, `uv.lock`, and the sources it installs, with the `README.md` and `LICENSE` their metadata names.

## 17. release-please: the manifest, pre-1.0 bumps and the history before the import

**Releases and versioning.** Now:

> `.release-please-manifest.json` holds the versions. It opens one release pull request, and merging it tags `<package>-v<version>`, updates each package's `CHANGELOG.md` and creates a GitHub release per package. Its `bootstrap-sha` is the import, so it never reads the old history.

Replace with:

> `.release-please-manifest.json` holds each package's last released version: its newest `<package>-v*` tag's, or `0.0.0` for a package never released, whose first release is then 0.1.0 (the python strategy's `initialReleaseVersion`; the default would be 1.0.0). release-please reads `0.1.0.dev0` as 0.1.0, so a pyproject version can't stand in. `bump-minor-pre-major` is on, so a breaking change bumps the minor version before 1.0, as the family's `!` commits always have; the default would release 1.0.0. It opens one release pull request, and merging it tags `<package>-v<version>`, updates each package's `CHANGELOG.md` and creates a GitHub release per package. It finds artifactr's last release by its imported tag, `artifactr-v0.1.0`, so no GitHub Release is needed in lattice. Its `bootstrap-sha` is the import: until every package has a release, it reads commits only back to there (release-please 17, `needsBootstrap`), so it never reads the old history.

## 18. The changelogs' history, under "Before lattice"

**Releases and versioning.** Now:

> **The changelogs' history is generated once.** The setup commit runs git-cliff from each package's directory, which scopes it to that directory, with `--tag-pattern "<package>-v.*"`. artifactr's `cliff.toml` skips eight prototype commits by SHA, so those SHAs are first mapped through filter-repo's `commit-map`. After that, git-cliff and every `cliff.toml` retire.

Replace with:

> **The changelogs' history is generated once.** The setup runs git-cliff in each package's rewritten clone, from the package's directory, which scopes it to that directory, with `--tag-pattern "<package>-v.*"`. artifactr's `cliff.toml` skips eight prototype commits by SHA, so those SHAs are first mapped through filter-repo's `commit-map`. A preprocessor links each rewritten reference to its repository's issue or pull request, mid-sentence too. What no release carries is headed "Before lattice", with no compare link. release-please reads nothing before the import, and inserts each release above the first heading that matches `\n###? v?[0-9[]`, which "## [Before lattice]" does, so those changes are listed there and nowhere else. After that, git-cliff and every `cliff.toml` retire.

## 19. The ruleset and the repository settings

**The day, step 3,** and **Decisions, Repository settings.** Replace "the required `CI` check" with "the required `CI` and `Title` checks".

## 20. grantr's and portalr's READMEs

**Migration.** Now:

> **grantr and portalr aren't imported.** Each holds one initial commit with a README and a license, and the setup commit copies the README's content.

Replace with:

> **grantr and portalr aren't imported.** Each holds one initial commit with a README and a license, and lattice's README carries what each README says. Their directories arrive with their code, since a `packages/*` member without a `pyproject.toml` stops uv.
