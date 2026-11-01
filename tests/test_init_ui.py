"""RFC 0003: rich TUI for ``reviewgraph install`` and ``reviewgraph init``."""

from __future__ import annotations

import argparse
import io
import subprocess
from pathlib import Path

import pytest
from reviewgraph import cli
from reviewgraph.init_ui import PlainReporter, RichReporter, make_reporter
from rich.console import Console


def _rich() -> tuple[RichReporter, io.StringIO]:
    ui = RichReporter("9.9.9")
    buf = io.StringIO()
    ui._console = Console(file=buf, force_terminal=True, width=100, color_system="standard")
    return ui, buf


def _tty(monkeypatch, value: bool) -> None:
    monkeypatch.setattr("sys.stdout.isatty", lambda: value, raising=False)


def test_plain_reporter_when_stdout_is_not_a_terminal(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    _tty(monkeypatch, False)
    assert isinstance(make_reporter("1.0"), PlainReporter)


def test_rich_reporter_on_a_colour_terminal(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    _tty(monkeypatch, True)
    assert isinstance(make_reporter("1.0"), RichReporter)


@pytest.mark.parametrize(
    "env,plain",
    [({"NO_COLOR": "1"}, False), ({"TERM": "dumb"}, False), ({}, True)],
)
def test_plain_reporter_when_colour_is_declined(monkeypatch, env, plain):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    _tty(monkeypatch, True)
    assert isinstance(make_reporter("1.0", plain=plain), PlainReporter)


def test_rich_rows_carry_colour_and_meaning():
    ui, buf = _rich()
    ui.start("install", detail="/home/me")
    with ui.step("Skills") as step:
        step.done("Generated skills in /x")
    with ui.step("Hooks") as step:
        step.skip("Skipped hooks (--no-hooks)")
    ui.would("create .reviewgraph/")
    ui.platforms(["claude", "cursor"])
    ui.finish(["  1. Restart your AI coding tool"])
    out = buf.getvalue()
    assert "\x1b[" in out
    for needle in ("ReviewGraph", "9.9.9", "✔", "–", "◌", "claude", "cursor", "Summary"):
        assert needle in out
    assert "1 done" in out and "1 skipped" in out and "0 failed" in out


def test_failed_step_is_red_listed_in_summary_and_reraised():
    ui, buf = _rich()
    with pytest.raises(RuntimeError, match="boom"):
        with ui.step("Hooks"):
            raise RuntimeError("boom")
    ui.finish(["  next"])
    out = buf.getvalue()
    assert "✘" in out
    assert out.count("boom") >= 2
    assert "1 failed" in out


def test_plain_step_prints_only_the_original_text_and_reraises(capsys):
    ui = PlainReporter()
    with ui.step("Skills") as step:
        step.done("Generated skills in /x")
    with pytest.raises(RuntimeError):
        with ui.step("Hooks"):
            raise RuntimeError("boom")
    assert capsys.readouterr().out == "Generated skills in /x\n"


def test_plain_finish_matches_the_legacy_next_steps(capsys):
    PlainReporter().finish(["  one", "  two"])
    assert capsys.readouterr().out == "\nNext steps:\n  one\n  two\n"


def test_rich_confirm_keeps_the_non_tty_contract(monkeypatch):
    ui, _ = _rich()
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)
    calls: list[bool] = []

    def fake(prompt: str, default_yes: bool = True) -> bool:
        calls.append(default_yes)
        return default_yes

    assert ui.confirm("Inject?", fake) is True
    assert calls == [True]


def _init_args(repo: Path, **over) -> argparse.Namespace:
    base = {"repo": str(repo), "dry_run": False, "no_build": True}
    base.update(over)
    return argparse.Namespace(**base)


def _git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def test_init_plain_output_is_the_legacy_log(tmp_path, capsys):
    repo = _git_repo(tmp_path)
    cli._handle_init(_init_args(repo))
    out = capsys.readouterr().out
    assert "\x1b" not in out
    assert out.splitlines()[0] == "Created .gitignore and added .reviewgraph/."
    assert "Skipped graph build (--no-build)." in out
    assert out.endswith(
        "\nNext steps:\n  reviewgraph install    # once per machine: set up your AI coding tools\n"
    )


def test_init_renders_through_rich_when_selected(monkeypatch, tmp_path):
    ui, buf = _rich()
    monkeypatch.setattr(cli, "make_reporter", lambda version, plain=False: ui)
    repo = _git_repo(tmp_path)
    cli._handle_init(_init_args(repo))
    out = buf.getvalue()
    for needle in ("ReviewGraph", "✔", "Summary", "reviewgraph install"):
        assert needle in out
    assert (repo / ".reviewgraph").is_dir()


def test_init_dry_run_renders_would_rows_and_writes_nothing(monkeypatch, tmp_path):
    ui, buf = _rich()
    monkeypatch.setattr(cli, "make_reporter", lambda version, plain=False: ui)
    repo = _git_repo(tmp_path)
    cli._handle_init(_init_args(repo, dry_run=True))
    assert buf.getvalue().count("◌") == 4
    assert not (repo / ".reviewgraph").exists()


def test_install_hook_failure_is_a_red_step_and_exit_is_unchanged(monkeypatch, tmp_path):
    ui, buf = _rich()
    monkeypatch.setattr(cli, "make_reporter", lambda version, plain=False: ui)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)

    def broken(_home):
        raise OSError("settings is read-only")

    monkeypatch.setattr("graph_engine.skills.install_gemini_cli_hooks", broken)
    args = argparse.Namespace(
        dry_run=False, platform="gemini-cli", yes=True, no_instructions=True,
        no_skills=True, no_hooks=False,
    )
    cli._handle_install(args)  # does not raise: same as before the TUI
    out = buf.getvalue()
    assert "✘" in out and "settings is read-only" in out and "1 failed" in out


def test_importing_the_cli_does_not_load_rich():
    """serve/mcp never style stdout: rich is loaded only when a reporter renders."""
    import sys

    code = "import sys, reviewgraph.cli; sys.exit(1 if 'rich' in sys.modules else 0)"
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0


def test_install_renders_banner_and_dry_run_note(monkeypatch, tmp_path):
    ui, buf = _rich()
    monkeypatch.setattr(cli, "make_reporter", lambda version, plain=False: ui)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    args = argparse.Namespace(
        dry_run=True, platform="all", yes=True, no_instructions=True,
        no_skills=True, no_hooks=True,
    )
    cli._handle_install(args)
    out = buf.getvalue()
    assert "ReviewGraph" in out and "[dry-run]" in out
