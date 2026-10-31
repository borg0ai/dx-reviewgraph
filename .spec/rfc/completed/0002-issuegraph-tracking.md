# RFC 0002: Replace Beads tracking with IssueGraph

**Status:** Implemented

## Summary

Replace repository Beads (`bd`) issue-tracking instructions and packaging/ignore references with IssueGraph. Remove obsolete `.beads/` configuration and hooks. Keep IssueGraph as sole task tracker, with tracked snapshots and ignored local database.

## Problem

The project no longer uses Beads. Leaving `bd` commands and `.beads/` rules in repository guidance points contributors at a retired tracker and conflicts with the user's IssueGraph workflow.

## Goals

- Make IssueGraph the only documented issue-tracking workflow.
- Remove obsolete Beads configuration, hooks, ignore rules, and package exclusions.
- Keep IssueGraph snapshots tracked while ignoring its local database.

## Non-goals

- Product code, CLI, runtime, storage-path, and user-facing brand changes; those belong to RFC 0001.
- Initializing IssueGraph data or creating/updating IssueGraph issues.
- Creating branches, committing, pushing, merging, or syncing IssueGraph remotes.

## Design

Update `AGENTS.md` and `CLAUDE.md` with IssueGraph commands and conservative Git ownership. Update root `.gitignore` to ignore IssueGraph local database files while allowing its snapshots and formulas to be tracked. Remove `.beads/` files and the obsolete Beads source-distribution exclusion from `modules/code-review/pyproject.toml`. Leave unrelated rebrand/code changes untouched.

## Acceptance

- Active agent instructions and packaging/ignore configuration contain no Beads, `bd`, `.beads`, or `.dolt` references.
- `.beads/` files are removed.
- `.gitignore` allows `.issuegraph/issues.jsonl`, `.issuegraph/manifest.json`, and formulas while ignoring local database state.
- Specify `validate` and `sync-check` pass.
- `git diff --check` passes.
