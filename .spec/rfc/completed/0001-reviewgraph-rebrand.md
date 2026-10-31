# RFC 0001: Rebrand Code Review Graph as ReviewGraph

**Status:** Implemented

## Summary

Rebrand the code review graph product as ReviewGraph across user-facing documentation, CLI output, generated integrations, and local state paths. Use `.reviewgraph/` for repository graph data, `.reviewgraphignore` for exclusions, and `~/.reviewgraph/` for per-user state. Remove the old product and storage names from active surfaces without adding compatibility aliases.

## Problem

The repository's active code, docs, and tests still contain the old Code Review Graph product identity and `.code-review-graph` state paths. Keeping those names after the user-facing rebrand makes setup, storage, and generated integration instructions inconsistent. The user explicitly requested ReviewGraph naming without the old duplicate identifiers.

## Goals

- Use ReviewGraph as product name across CLI messages, documentation, action output, hooks, skills, and generated configuration.
- Rename repository and user state paths and ignore-file names to `.reviewgraph` conventions.
- Align tests and packaging checks with the new names.
- Remove the obsolete VS Code extension and its build, packaging, and documentation references where still present.

## Non-goals

- Changing ReviewGraph product functionality or MCP/CLI command semantics beyond naming and state-path behavior.
- Retaining compatibility aliases for old product or state-path names.
- Replacing IssueGraph or modifying its issue data; that work belongs to RFC 0002.
- Creating branches, committing, pushing, merging, or syncing remotes.

## Design

Update product-facing docs, CLI output, generated hooks/instructions, and tests to use ReviewGraph branding. Rename repository-local data, per-user data, and ignore-file conventions to `.reviewgraph`; update root ignore rules, path discovery, setup messages, and tests together. Keep historical changelog and released-artifact fixtures where they document prior versions, and ensure no compatibility behavior is introduced for the retired names. Remove VS Code extension references if any remain. Do not include IssueGraph tracker migration here.

## Acceptance

- Active product documentation, CLI output, generated integration content, storage paths, and tests consistently use ReviewGraph names.
- New repositories initialized by the CLI use `.reviewgraph/`; graph lookup and ignore-file discovery use the corresponding ReviewGraph names.
- No compatibility aliases are added for the retired product or state-path names.
- Obsolete VS Code extension files, CI checks, and packaging references are absent.
- Existing tests cover initialization, path detection, and ignore behavior with the new names.
- Specify `validate` passes for this RFC and `sync-check` reports consistent RFC, roadmap, and task tracking.
- `git diff --check` passes.
