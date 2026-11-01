# Why: feat-rfc-0003-init-tui

<!-- reasongraph:v1 generated 2026-11-01 — review before sharing; edit freely, edits are preserved -->

## Intent
Create a feature branch for RFC 0003 initialization TUI work and open a pull request.

## Decisions

### Create feature branch from main for RFC 0003
Status: directed
Touches: `.git/refs/heads/feat/rfc-0003-init-tui`

The branch isolates RFC 0003 changes for pull request review. It is based on `main` and carries the existing local commits.

### Push feature branch to origin
Status: directed
Touches: `.git/refs/remotes/origin/feat/rfc-0003-init-tui`

Pushing the branch publishes the changes so a pull request can be opened and reviewed.

### Install wheel dependencies through pip
Status: discussed
Touches: `Formula/reviewgraph.rb`

The formula installs both wheels with regular `pip install` because Homebrew's `venv.pip_install` omitted their dependencies, causing `reviewgraph init` to fail on missing modules such as `networkx`. The formula fix was pushed to `develop` as commit `d7598aa`.

### Create a rich terminal UI for init
Status: directed
Touches: `.spec/rfc/0003-init-tui.md`, `apps/cli/reviewgraph/cli.py`

The draft RFC specifies a colorful terminal interface for `reviewgraph init`, with per-step progress, platform details, confirmation, and a final summary. It uses `rich`, already present transitively in `uv.lock`, and assigns green to completed steps, yellow to skipped steps, and red to failures.

### Keep init and install behavior unchanged pending a decision
Status: discussed
Touches: `.spec/rfc/0003-init-tui.md`, `apps/cli/reviewgraph/cli.py`

The draft limits the change to terminal presentation and retains plain output for non-TTY runs. The RFC is still Draft and implementation has not started, so existing init and installation behavior remains the baseline until approval.
