# Agent Instructions

Project context (architecture, commands, conventions, tests) is in `CLAUDE.md`. This file holds the rules for every coding agent working in this repository.

## Non-Interactive Shell Commands

`cp`, `mv` and `rm` may be aliased with `-i` on some systems, which leaves an agent waiting for a y/n answer that never comes. Always pass the non-interactive flag:

```bash
cp -f source dest
mv -f source dest
rm -f file
rm -rf directory
cp -rf source dest
```

Other commands that may prompt: `scp` and `ssh` (`-o BatchMode=yes`), `apt-get` (`-y`), `brew` (`HOMEBREW_NO_AUTO_UPDATE=1`).

## IssueGraph issue tracking

This project uses IssueGraph. Run `issuegraph prime` for current workflow and command guidance.

```bash
issuegraph ready
issuegraph show <id>
issuegraph update <id> --claim
issuegraph close <id>
issuegraph remember "insight"
```

- Use IssueGraph for task tracking. Do not create Markdown TODO lists.
- IssueGraph stores the local database under `.issuegraph/` and tracks `issues.jsonl` plus `manifest.json` in Git.
- Do not create branches, commit, push, merge, or sync IssueGraph remotes unless the user explicitly asks. When asked for a PR, target `main`.
- Before handoff, run relevant quality checks and report changed files and validation results.

<!-- reviewgraph MCP tools -->
## MCP Tools: reviewgraph

**This project has a knowledge graph. Start with the reviewgraph
MCP tools to narrow scope, then read the source.** The graph is cheaper than scanning files and
gives you structural context (callers, dependents, test coverage) that file search cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes_tool` or `query_graph_tool` instead of Grep
- **Understanding impact**: `get_impact_radius_tool` instead of manually tracing imports
- **Code review**: `detect_changes_tool` + `get_review_context_tool` instead of reading entire files
- **Finding relationships**: `query_graph_tool` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview_tool` + `list_communities_tool`

### Verify in the source

- Narrow scope with the graph, then read the source. Do not change code from graph output alone.
- For any non-trivial change, read the implementation and the relevant tests before concluding.
- Verify the exact source when touching behavior, database logic, migrations, retries, fallbacks,
  recovery, or compatibility code.
- When the graph and the source disagree, the source wins. The graph may be stale or may not
  model that relationship.
- An empty graph result can mean "not indexed" or "not statically visible", not "does not exist".

### Key Tools

| Tool | Use when |
| ------ | ---------- |
| `detect_changes_tool` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context_tool` | Need source snippets for review — token-efficient |
| `get_impact_radius_tool` | Understanding blast radius of a change |
| `get_affected_flows_tool` | Finding which execution paths are impacted |
| `query_graph_tool` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes_tool` | Finding functions/classes by name or keyword |
| `get_architecture_overview_tool` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes_tool` for code review.
3. Use `get_affected_flows_tool` to understand impact.
4. Use `query_graph_tool` pattern="tests_for" to check coverage.
<!-- /reviewgraph MCP tools -->

<!-- reasongraph:begin -->
## Design reasoning lives in `.reasongraph/why/`

This repo records the *why* behind its code in `.reasongraph/why/<branch>.md` ("why-packs"),
distilled from AI coding sessions. **The why-pack is the ground truth for *why* —
prefer it over commit messages, which are lossy and can be out of date.**

- Before working on unfamiliar code, run `reasongraph context <file>` (or grep
  `.reasongraph/why/`) to see the decisions that touch it.
- When asked what changed on a branch, or *why* something is the way it is, read
  `.reasongraph/why/<branch>.md` — not just `git log`.
- `grep -rn "agent-initiated" .reasongraph/why/` surfaces decisions an agent made
  unilaterally, with no human sign-off — scrutinize these first.

Commits titled `reasongraph: update why-pack (…)` are written by the tool (the
why-pack only, via a scratch index — they never touch your staged work). They're
safe to rebase past or drop; don't amend them into your feature commits.
<!-- reasongraph:end -->

<!-- BEGIN ISSUEGRAPH INTEGRATION v:1 profile:minimal hash:dc6921e9 -->
## IssueGraph Issue Tracker

This project uses **issuegraph (IssueGraph)** for issue tracking. Run `issuegraph prime` to see full workflow context and commands.

### Quick Reference

```bash
issuegraph ready              # Find available work
issuegraph show <id>          # View issue details
issuegraph update <id> --claim  # Claim work
issuegraph close <id>         # Complete work
```

### Rules

- Use `issuegraph` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `issuegraph prime` for detailed command reference and session close protocol
- Use `issuegraph remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.issuegraph/issues.jsonl` is a passive export. See https://github.com/borg0ai/dx-issuegraph/blob/main/docs/core-concepts/sync-concepts.md for details and anti-patterns.

## Agent Context Profiles

The managed IssueGraph block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `issuegraph` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `issuegraph prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close issuegraph, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a IssueGraph implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create issuegraph for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this IssueGraph block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END ISSUEGRAPH INTEGRATION -->

<!-- BEGIN ISSUEGRAPH CODEX SETUP: generated by issuegraph setup codex -->
## IssueGraph Issue Tracker

Use IssueGraph (`issuegraph`) for durable task tracking in repositories that include it. Use the `issuegraph` skill at `.agents/skills/issuegraph/SKILL.md` (project install) or `~/.agents/skills/issuegraph/SKILL.md` (global install) for IssueGraph workflow guidance, then use the `issuegraph` CLI for issue operations.

### Quick Reference

```bash
issuegraph ready                # Find available work
issuegraph show <id>            # View issue details
issuegraph update <id> --claim  # Claim work
issuegraph close <id>           # Complete work
issuegraph prime                # Refresh IssueGraph context
```

### Rules

- Use `issuegraph` for all task tracking; do not create markdown TODO lists.
- Run `issuegraph prime` when IssueGraph context is missing or stale. Codex 0.129.0+ can load IssueGraph context automatically through native hooks; use `/hooks` to inspect or toggle them.
- Keep persistent project memory in IssueGraph via `issuegraph remember`; do not create ad hoc memory files.

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.issuegraph/issues.jsonl` is a passive export. See https://github.com/borg0ai/dx-issuegraph/blob/main/docs/core-concepts/sync-concepts.md for details and anti-patterns.
<!-- END ISSUEGRAPH CODEX SETUP -->
