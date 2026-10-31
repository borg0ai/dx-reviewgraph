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
