# Why: main

<!-- reasongraph:v1 generated 2026-11-01 — review before sharing; edit freely, edits are preserved -->

## Intent
Rename ReviewGraph engine distribution and module paths, repair Homebrew installation, and separate global agent setup from repository initialization while preparing a rich TUI for both commands.

## Decisions

### Rename engine distribution to reviewgraph-engine
Status: directed
Touches: `modules/reviewgraph/pyproject.toml`, `apps/cli/pyproject.toml`, `pyproject.toml`, `uv.lock`, `tests/test_packaging.py`, `tests/test_genai_packaging.py`, `tests/test_optional_dependencies.py`

The engine distribution name was changed from `code-review-engine` to `reviewgraph-engine` so its wheel uses the product name. The CLI remains the separate `reviewgraph` distribution, while the Python import package remains `graph_engine`.

Considered/rejected: Using `reviewgraph` for the engine would collide with the CLI distribution.

### Rename engine module directory to modules/reviewgraph
Status: directed
Touches: `modules/code-review`, `modules/reviewgraph`, `pyproject.toml`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/*`, `README*`, `scripts/*`, `.github/PULL_REQUEST_TEMPLATE.md`, `tests/*`

The module directory and its path references were renamed to align repository structure with the ReviewGraph product name. The `graph_engine` import package and historical changelog references were retained to avoid unnecessary compatibility and history changes.

### Publish the renamed distribution as version 2.3.11
Status: discussed
Touches: `pyproject.toml`, `*/pyproject.toml`

The release preflight found version `2.3.11` in the latest tag and all three package manifests, so a new release requires a version bump. The proposed `2.4.0` and alternative `2.3.12` were not selected; no release changes were made.

### Install Homebrew wheel dependencies and test graph construction
Status: discussed
Touches: `Formula/reviewgraph.rb`

The formula uses plain `pip install` for both wheels because Homebrew’s `pip_install` ran with `--no-deps`, leaving runtime dependencies such as `networkx` unavailable. The CLI version command still worked because it imports the graph engine lazily.

### Separate global install from repository initialization
Status: discussed
Touches: `.spec/rfc/0004-install-init-split.md`, `.spec/rfc/0003-init-tui.md`, `.spec/ROADMAP.md`, `.spec/TASK_TRACKING.md`, `skills.py`, `apps/cli/reviewgraph/cli.py`

The drafted RFC assigns global agent setup to `install` and repository seeding to `init`. This keeps global configuration writes out of repositories and prevents repository initialization from installing agent configuration.

### Render install and init with a rich colorful TUI
Status: discussed
Touches: `.spec/rfc/0003-init-tui.md`, `apps/cli/reviewgraph/cli.py`

The drafted RFC specifies rich terminal output for both commands, with step status, platform details, confirmation, and a summary. Semantic colors distinguish completed, skipped, and failed steps.

### Add reporter abstraction for install and init output
Status: discussed
Touches: `apps/cli/reviewgraph/init_ui.py`, `apps/cli/reviewgraph/cli.py`, `tests/test_init_ui.py`

A shared reporter interface supports rich and plain output across both commands. Steps record completion, skips, and failures; failed steps preserve exception behavior unless that operation was already caught by the command.

### Initialize graph indexes in the working repository
Status: discussed
Touches: `.spec/rfc/0004-install-init-split.md`, `apps/cli/reviewgraph/cli.py`

The drafted initialization flow seeds the repository and runs `build` to create graph indexes and report graph statistics. The existing handler only printed build as a next step, so the RFC makes graph construction part of initialization.

### Do not update the netify plugin automatically
Status: discussed
Touches: `~/.claude/plugins/marketplaces/netify`

插件目录包含本地配置改动，更新可能与其冲突。插件更新会改变执行 skill-check 的钩子，因此由本地操作者处理。

### Preserve local marketplace configuration changes
Status: discussed
Touches: `~/.claude/plugins/marketplaces/netify/marketplace.json`

marketplace.json 有本地改动；拉取更新可能产生冲突，因此保留现有配置并避免自动更新。

### Declare Rich as a CLI dependency
Status: discussed
Touches: `apps/cli/pyproject.toml`, `uv.lock`

The CLI declares Rich as a dependency for interactive rendering, and the workspace lockfile records the dependency.

### Keep Rich unloaded when importing the CLI
Status: discussed
Touches: `apps/cli/reviewgraph/init_ui.py`, `apps/cli/reviewgraph/cli.py`, `tests/test_init_ui.py`

Rich imports stay inside reporter methods so importing `reviewgraph.cli` does not load Rich or add styled output to MCP stdio.

### Preserve existing hook failure behavior
Status: discussed
Touches: `apps/cli/reviewgraph/cli.py`, `tests/test_init_ui.py`

The init git hook failure path remains unchanged to preserve its existing exception and exit behavior. The new red-step failure coverage targets the install hook path, whose failure is already caught and logged.

### Use TDD for the init TUI
Status: discussed
Touches: `apps/cli/reviewgraph/init_ui.py`, `apps/cli/reviewgraph/cli.py`, `tests/test_init_ui.py`

The init TUI changes were scoped to RFC 0003. The recorded validation included Ruff, mypy, and 4,968 passing pytest cases; seven known failures were reported as unrelated.

### Preserve byte-for-byte plain output
Status: discussed
Touches: `apps/cli/reviewgraph/init_ui.py`, `apps/cli/reviewgraph/cli.py`, `tests/test_init_ui.py`

Noninteractive, `NO_COLOR`, `TERM=dumb`, and `--plain` runs use the plain reporter to retain legacy output. Tests compare init output against the legacy log and cover the non-TTY confirmation contract.

### Lock dependencies with Python 3.13
Status: discussed
Touches: `uv.lock`, `apps/cli/pyproject.toml`

The lock update explicitly used Python 3.13 after an earlier resolution selected Python 3.15. The resulting lockfile diff added two lines.

### Document init terminal output
Status: discussed
Touches: `docs/USAGE.md`

The RFC 0003 documentation update covers terminal output from init so the command’s user-visible behavior is documented.

### Archive RFC 0003 after implementation
Status: discussed
Touches: `.spec/ROADMAP.md`, `.spec/TASK_TRACKING.md`, `.spec/rfc/0003-init-tui.md`

The RFC files were included in the intended commit scope, and `specify sync-check` was reported successful with no errors or warnings.

### Commit RFC 0003 changes by explicit path
Status: directed
Touches: `apps/cli/reviewgraph/init_ui.py`, `apps/cli/reviewgraph/cli.py`, `apps/cli/pyproject.toml`, `uv.lock`, `tests/test_init_ui.py`, `docs/USAGE.md`, `.spec/ROADMAP.md`, `.spec/TASK_TRACKING.md`, `.spec/rfc/0003-init-tui.md`

The commit scope was limited to ten paths from RFC 0003 so unrelated staged changes would remain untouched. Commit did not complete: the Netify hook blocked each attempt because required capability-table evidence was not recognized.

### Do not bypass the Netify hook
Status: discussed
Touches: `netify-skill-check.mjs`

The agent left the hook enabled after it blocked write operations because its required skill-check table was absent from the recorded transcript. The RFC 0003 implementation therefore remained unstarted.

### Commit implementation before RFC lifecycle changes
Status: discussed
Touches: `README*`, `docs/**`, `CHANGELOG*`, `action.yml`, `release_gate*`, `embeddings*`, `eval*`, `*.md`

The agent staged all pending working-tree changes and committed them together on `main`, after aligning the branch with `origin/main` at `7461013`. The commit recorded 37 changed files, with 464 insertions and 1,317 deletions.

### Install formula wheels with dependencies
Status: discussed
Touches: `Formula/reviewgraph.rb`

The formula installs both wheels with plain `pip install` so pip resolves and installs their declared dependencies. Homebrew’s `venv.pip_install` uses `--no-deps`, which left packages such as `networkx` unavailable when `reviewgraph init` ran.

Considered/rejected: Using `venv.pip_install` was rejected because it omits wheel dependencies.

### Commit all pending changes on main
Status: directed
Touches: `CHANGELOG.md`, `*/README*`, `action.yml`, `pyproject.toml`, `scripts/release_gate.py`, `diagnose_pypi_connectivity.py`, `test_upgrade_path.py`

The pending 37-file change set was committed on `main` and pushed as `abb440c` after its diff was inspected. This brought the requested working-tree changes into the shared branch.

### Commit all pending changes on main
Status: discussed — release handling proposed, not confirmed
Touches: `.reasongraph/why/main.md`

The generated why-pack file and its local commit leave the working tree ahead of `origin/main`, blocking the release preflight. Including the generated file in a release commit was proposed because the pre-push hook regenerates it, but this handling remains undecided.

Risk: Release remains blocked while local and remote branch state differ.
