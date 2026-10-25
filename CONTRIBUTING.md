# Contributing to ReviewGraph

## Development Setup

```bash
git clone https://github.com/borg0ai/dx-reviewgraph.git
cd dx-reviewgraph
uv sync --group dev                  # requires uv
uv run pytest tests/ --tb=short -q   # check the setup
```

## Running Tests

```bash
uv run pytest tests/ --tb=short -q                                                    # all tests
uv run pytest --cov=graph_engine --cov-report=term-missing --cov-fail-under=65   # with the CI coverage gate
uv run pytest tests/test_parser.py -v                                                 # one file
```

CI runs the suite on Python 3.10, 3.11, 3.12 and 3.13 and fails below 65% coverage.

`tests/test_parser_grammar_contract.py` checks every built-in class, function, import,
and call dispatch name against its bundled Tree-sitter grammar. When updating a grammar
or adding dispatch entries, use the grammar's actual named node types. This contract
checks configured dispatch names; language fixtures still verify extraction behavior.

## Linting and Type Checking

```bash
uv run ruff check modules/code-review/graph_engine/ apps/cli/reviewgraph/
uv run mypy modules/code-review/graph_engine/ apps/cli/reviewgraph/ --ignore-missing-imports --no-strict-optional
```

CI also runs `bandit -r modules/code-review/graph_engine/ -c pyproject.toml`.

## Code Style

- Line length: 100 characters.
- Target: Python 3.10+.
- Linter: ruff with rules E, F, I, N, W. Imports are sorted by ruff.
- SQL: parameterised queries (`?` placeholders) only.

## Making Changes

1. Fork the repository and create a branch from `main`: `git switch -c feature/your-feature origin/main`.
2. Make the change and add tests for new behaviour.
3. Run the tests, ruff and mypy as above.
4. Update docs where behaviour changed (README, `docs/`, docstrings).
5. Open a pull request against `main`. The template asks for the linked issue, what changed and why, and the commands you ran.

## Branching

Create a short-lived feature branch from `origin/main` and send every change
through a pull request directly to `main`:

```bash
git fetch origin
git switch -c feature/your-change origin/main
```

Run the checks listed in Development Setup, then open a PR against `main`. CI and the
ReviewGraph PR review workflow run on the PR. Merge through GitHub. Tag releases from `main`.

The optional release gate is separate from routine PR CI. Run
`.github/workflows/release-gate.yml` manually before a release when slow upgrade,
packaging, determinism, E2E, corpus and browser checks are needed. It reports to the
workflow summary and a `release-gate` issue; it does not open or merge pull requests.

## Project Structure

The module list is in the Architecture section of `CLAUDE.md`. In outline:

```
apps/cli/pyproject.toml                 # CLI application package and entry points
apps/cli/reviewgraph/               # reviewgraph and reviewgraph-daemon commands
modules/code-review/pyproject.toml       # reusable core module package
modules/code-review/graph_engine/        # core library, MCP server, tools and eval
modules/code-review/skills/             # skills bundled into the core wheel
tests/                                  # pytest suite and language fixtures
docs/                                   # user documentation
```

## Adding Language Support

If you only need a language for your own repository, you may not need to change this project: add a `.code-review-graph/languages.toml` that maps extensions and node types to any grammar in tree-sitter-language-pack (see [docs/CUSTOM_LANGUAGES.md](docs/CUSTOM_LANGUAGES.md)). To add built-in support:

1. Add the extension mapping to `EXTENSION_TO_LANGUAGE` in `parser.py`.
2. Add the tree-sitter node types to `_CLASS_TYPES`, `_FUNCTION_TYPES`, `_IMPORT_TYPES` and `_CALL_TYPES`.
3. Add a sample file in `tests/fixtures/`.
4. Add parsing tests in `tests/test_multilang.py`.

## Adding a Platform Target

Every supported AI tool is permanent maintenance surface: its config path, schema, install merge, uninstall and tests have to keep working on every release. Some existing targets were merged without evidence that they worked in a released client, and those are the ones that break. New targets are held to the bar below.

Start with a platform request issue (https://github.com/borg0ai/dx-reviewgraph/issues/new/choose) so the client can be discussed before anyone writes code. A pull request that adds a platform will not be reviewed until it includes all of the following.

1. A link to the platform's official MCP configuration documentation. Blog posts, forum replies and screenshots of a settings dialog are not enough.
2. The exact config file path and the exact schema of a server entry: which top-level key holds the servers, whether that value is an object or an array, and whether a `type` field is required.
3. The entry added through the existing `PLATFORMS` table in `modules/code-review/graph_engine/skills.py`, plus `_PLATFORM_CHOICES` in `apps/cli/reviewgraph/cli.py`. Use the fields already there: `name`, `config_path`, `key`, `detect`, `format`, `needs_type`, and where needed `legacy_keys`, `server_type`, `entry_fields`. If the client needs something the table cannot express, say so in the pull request and explain why, rather than adding a separate code path beside it.
4. Preservation of unrelated user settings. Install must merge only the `reviewgraph` server entry and leave every other server, key and top-level setting intact. If the file cannot be parsed, install must skip it rather than rewrite it.
5. A byte-idempotent reinstall. Running install twice must leave the config file and any generated instruction file byte for byte identical.
6. A working uninstall in `modules/code-review/graph_engine/uninstall.py` that removes only what install added, including any legacy keys, and leaves the rest of the file untouched.
7. Lifecycle tests matching the existing ones: an install, reinstall and uninstall test in `tests/test_cli_install.py` shaped like `test_copilot_cli_install_reinstall_uninstall_lifecycle`, and a passing run of the all-platforms sweep in `tests/test_uninstall.py` (`test_uninstall_removes_mcp_entry_for_every_current_platform_spec`), which covers every new entry automatically.
8. Evidence from a real released client: a screenshot or transcript of a session in that client where a reviewgraph tool is invoked and returns a result. A rendered image of text, a mockup or a description of what should happen is not evidence.

If no maintainer can install and run the client, the request may be declined or left open until someone who uses it is willing to own it and respond when it breaks. An existing target may also be removed if it breaks and nobody steps up to fix it.

## Reporting Issues

- Open an issue through the issue forms: https://github.com/borg0ai/dx-reviewgraph/issues/new/choose (bug report, feature request or platform request; blank issues are disabled).
- For questions and ideas, use GitHub Discussions: https://github.com/borg0ai/dx-reviewgraph/discussions
- Include your Python version, OS, steps to reproduce and the error output.

## License

By contributing, you agree that your contributions are licensed under the MIT License.
