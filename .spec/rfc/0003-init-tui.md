# RFC 0003: Refine reviewgraph init as a rich colorful TUI

**Status:** Approved

## Summary

`reviewgraph install` and `reviewgraph init` (today one shared handler `_handle_init` in `apps/cli/reviewgraph/cli.py`, split into agent setup and repo seed by RFC 0004) print about 20 unstyled `print()` lines. Replace that with a rich, colorful terminal UI on an interactive terminal, for both commands: a banner, a live per-step progress view, a platform table, a styled confirm prompt and a closing summary panel. Non-interactive runs (pipes, CI, MCP wrappers, `NO_COLOR`) keep today's plain log output unchanged.

## Problem

Install and init are the first things a user runs and they look like a debug log. It configures up to 16 platforms, writes skills, hooks, instruction files and a git hook, but the output is a flat stream of lines such as `Installed hooks in .claude/settings.json`. Nothing shows progress, what was skipped, what failed or what to do next. The only prompt is a bare `input()` `[Y/n]`. A failure is a `logger.warning` line that scrolls past.

## Goals

- On a TTY, `install` and `init` render: header banner (name, version, repo root), one live-updating row per step (pending, running, done, skipped, failed), a table of platforms with detected / configured state, a styled instruction-injection confirm, and a final summary panel with next steps.
- Colour carries meaning: green done, yellow skipped or user-declined, red failed, dim for paths. Respects `NO_COLOR` and a dumb terminal.
- Failures stay visible in the summary with their reason, not only in the log.
- Behaviour is unchanged: same files written, same flags (`--dry-run`, `--yes`, `--platform`, `--no-skills`, `--no-hooks`, `--no-instructions`), same exit codes.

## Non-goals

- Changing what init installs or which platforms are supported.
- A full-screen app or a keyboard-driven platform picker. Platform choice stays on `--platform`.
- Restyling other commands (`build`, `update`, `status`). A shared helper may make that easy later; it is out of scope here.
- Changing MCP server output. stdio JSON-RPC must never receive styled output.

## Design

Library: use `rich` (Live, Progress, Table, Panel, Confirm). It is already in `uv.lock` as a transitive dependency. Declare it explicitly in `apps/cli/pyproject.toml` so the CLI does not depend on a transitive pin.

Structure, inside `apps/cli/reviewgraph/`:

- New `init_ui.py`: a small reporter with one interface, `step(label)` (context manager that marks running, then done, failed or skipped), `note(text)` and `summary(...)`. Two implementations: `RichReporter` and `PlainReporter`. `PlainReporter` prints exactly the current strings, so existing output and tests stay valid.
- `_handle_init` stops calling `print()` directly and reports through the reporter. The install calls (`install_platform_configs`, `generate_skills`, `inject_instruction_files`, `install_*_hooks`, `install_git_hook`) are not modified; the handler only wraps them and records outcomes.
- Selection: `RichReporter` only when `sys.stdout.isatty()`, `NO_COLOR` is unset, `TERM` is not `dumb`, and a new `--plain` flag is absent. Otherwise `PlainReporter`. `_supports_color()` already holds part of this check and is reused.
- Confirm: `_confirm_yes_no` keeps its non-TTY contract (return the default without reading stdin, see #173 and #174). On a TTY the rich reporter shows the file list as a table and asks with a styled prompt.
- Dry run renders the same steps marked "would", so `--dry-run` is previewable in colour too.
- Exceptions caught today with `logger.warning` are also recorded as failed steps and listed in the summary panel.

Files touched: `apps/cli/reviewgraph/cli.py`, new `apps/cli/reviewgraph/init_ui.py`, `apps/cli/pyproject.toml`, `uv.lock`, tests, and the `init` section of `docs/USAGE.md`.

## Acceptance

- On a pseudo-terminal, `reviewgraph init` in a scratch git repo shows the banner, per-step rows, a platform table and the summary panel, with colour.
- With stdout piped, `NO_COLOR=1`, `TERM=dumb` or `--plain`, output is byte-for-byte the current plain output; a regression test pins this.
- `--dry-run`, `--yes`, `--platform`, `--no-skills`, `--no-hooks` and `--no-instructions` write the same files as before; the existing `tests/test_cli_install.py` and `tests/test_cli*.py` pass unmodified.
- A forced hook failure appears as a red step and in the summary, and the exit code is unchanged.
- No ANSI escape sequence reaches stdout when the process runs as an MCP stdio server.
- `uv run ruff check`, `uv run mypy` and the full test suite pass.
- Specify `validate` and `sync-check` pass.
