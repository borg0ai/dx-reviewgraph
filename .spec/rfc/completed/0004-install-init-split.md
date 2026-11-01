# RFC 0004: Split install and init: global agents vs repo seed

**Status:** Implemented

## Summary

Today `reviewgraph init` is "Alias for install": both run `_handle_init` and write a mix of user-level and repo-level files, and neither builds the graph. Give each command one job. `reviewgraph install` configures the AI agents globally and writes nothing into a repository. `reviewgraph init` seeds the current repository (`.reviewgraph/`, ignore rule, git hook) and builds the graph, and installs nothing for any agent.

## Problem

- One command does two jobs, so users cannot set up their machine once and then prepare many repositories.
- `install` writes into the repo: `.mcp.json`, `.cursor/mcp.json`, `.gemini/settings.json`, `.kiro/`, `.qoder/`, `.vscode/mcp.json`, `.claude/settings.json` hooks, instruction blocks in `CLAUDE.md` and `AGENTS.md`, and a git pre-commit hook. These land in version control or dirty the working tree of every project.
- Other platforms already write globally (Codex `~/.codex/config.toml`, Windsurf, Continue, Antigravity, Qwen, Copilot CLI, Hermes, the OpenCode plugin, Cursor hooks), so behaviour differs per agent.
- `init` never builds. The user is told to run `reviewgraph build` as a second step.

## Goals

- `install` is repo-independent: runnable from any directory, writes only user-level locations (agent MCP config, skills, hooks, global instruction files), never touches the current repository.
- `init` is agent-independent: creates `.reviewgraph/`, adds `.reviewgraph/` to `.gitignore`, installs the git pre-commit hook, runs `build`, and ends by printing the graph statistics. It reads and writes no agent configuration.
- `init --no-build` seeds without building.
- The split mirrors `reasongraph install` (agents) and `reasongraph init` (repo seed).
- Both commands report through the TUI reporter from RFC 0003, with the same plain fallback.

## Non-goals

- Changing what the MCP server, `build` or `update` do.
- Adding platforms or changing the MCP entry written for each platform.
- Per-repo agent config as a supported mode. A user who wants it can commit config by hand.

## Design

Handler split in `apps/cli/reviewgraph/cli.py`: `_handle_install` (agent side) and `_handle_init` (repo side). `init` stops being an alias; the parser registers two distinct commands with their own flags.

`install` keeps `--platform`, `--dry-run`, `--yes`, `--no-skills`, `--no-hooks`, `--no-instructions`. It loses `--repo`. For each platform the target path must be user-level:

- Already user-level: codex, windsurf, zed, continue, opencode, antigravity, qwen, copilot-cli, hermes, plus the OpenCode plugin and Cursor hooks. No change.
- Move from repo to user-level: claude (`~/.claude.json` user scope instead of `.mcp.json`; hooks into `~/.claude/settings.json`), cursor (`~/.cursor/mcp.json`), gemini-cli (`~/.gemini/settings.json`), codebuddy, qoder, vscode (user settings), kiro (`~/.kiro/settings/mcp.json`).
- Instruction blocks go to each agent's user-level instruction file (for example `~/.claude/CLAUDE.md`), never `CLAUDE.md` in the repo.
- A platform that has no user-level location is reported as skipped with the reason, not written into the repo.

`init` keeps `--repo` and `--dry-run`, and adds `--no-build`. Steps: ensure `.reviewgraph/`, ensure the `.gitignore` entry, install the git pre-commit hook (`install_git_hook`), run the full build. It never imports `PLATFORMS`.

Migration: an upgrade leaves previously written repo files alone. `reviewgraph uninstall` keeps removing both old repo-level and new user-level entries so existing users can clean up. `docs/USAGE.md`, `docs/FEATURES.md` and `docs/ROADMAP.md` (both still call `init` an alias) and the release notes describe the new flow: `reviewgraph install` once, `reviewgraph init` per repo.

Open points to settle before implementation:

- Exact user-level path and merge rules per moved platform, verified against each agent's documentation.
- Whether `init` should warn when `install` has never been run (no MCP config found anywhere).

## Acceptance

- `reviewgraph install` run from a directory that is not a repo succeeds and creates or modifies no file under that directory; a test snapshots the working tree before and after.
- `reviewgraph install` inside a repo leaves `git status` clean.
- `reviewgraph init` in a scratch git repo creates `.reviewgraph/graph.db`, updates `.gitignore`, installs the pre-commit hook, and writes no agent config file (no `.mcp.json`, `.cursor/`, `.claude/`, `.gemini/`, `.kiro/`, `.qoder/`, `.vscode/mcp.json`, `CLAUDE.md` or `AGENTS.md` changes).
- `reviewgraph init --no-build` creates the seed without a graph database.
- `uninstall` removes both the old repo-level entries and the new user-level entries.
- Existing tests are updated to the new split; `test_installer_ownership.py`, `test_platform_lifecycle.py` and `test_uninstall.py` still pass.
- `uv run ruff check`, `uv run mypy`, the full suite, Specify `validate` and `sync-check` pass.
