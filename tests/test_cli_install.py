"""Tests for install CLI platform-specific behavior."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from graph_engine import skills, uninstall
from reviewgraph.cli import _handle_init, _handle_install


def _args(tmp_path: Path, platform: str) -> argparse.Namespace:
    return argparse.Namespace(
        repo=str(tmp_path),
        dry_run=False,
        platform=platform,
        yes=True,
        no_instructions=True,
        no_skills=False,
        no_hooks=False,
    )


def test_copilot_cli_install_reinstall_uninstall_lifecycle(
    monkeypatch, tmp_path
):
    """The public lifecycle migrates safely and is repeatable without a client."""
    repo = tmp_path / "repo"
    (repo / ".git" / "hooks").mkdir(parents=True)
    home = tmp_path / "home"
    config = home / ".copilot" / "mcp-config.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "current-server": {"command": "keep-current"},
                },
                "servers": {
                    "reviewgraph": {},
                    "legacy-server": {"command": "keep-legacy"},
                },
                "theme": "dark",
            }
        ),
        encoding="utf-8",
    )
    legacy_instruction = repo / ".github" / "graph_engine.instruction.md"
    legacy_instruction.parent.mkdir(parents=True)
    legacy_instruction.write_text(
        "# User notes\n\n" + skills._COPILOT_SECTION,
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: home)
    args = _args(repo, "copilot-cli")
    args.no_instructions = False
    args.no_skills = True
    args.no_hooks = True

    _handle_install(args)
    first_config = config.read_bytes()
    current_instruction = (
        repo
        / ".github"
        / "instructions"
        / "graph_engine.instructions.md"
    )
    _handle_install(args)

    assert config.read_bytes() == first_config
    # install is user-level only (RFC 0004): it never writes or migrates repo files.
    assert not current_instruction.exists()
    assert skills._COPILOT_SECTION in legacy_instruction.read_text(encoding="utf-8")
    installed = json.loads(config.read_text(encoding="utf-8"))
    assert installed["mcpServers"]["current-server"] == {
        "command": "keep-current",
    }
    assert installed["mcpServers"]["reviewgraph"]["type"] == "local"
    assert installed["mcpServers"]["reviewgraph"]["tools"] == ["*"]
    assert installed["servers"] == {
        "legacy-server": {"command": "keep-legacy"},
    }

    report = uninstall.run(repo=repo, keep_data=True)

    assert report.errors == []
    assert json.loads(config.read_text(encoding="utf-8")) == {
        "mcpServers": {
            "current-server": {"command": "keep-current"},
        },
        "servers": {
            "legacy-server": {"command": "keep-legacy"},
        },
        "theme": "dark",
    }
    assert legacy_instruction.read_text(encoding="utf-8") == "# User notes\n"
    assert not current_instruction.exists()


def test_handle_install_codex_skips_claude_skills(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        "graph_engine.skills.install_platform_configs",
        lambda repo_root, target, dry_run=False, user_scope=False: ["Codex"],
    )

    called = {"generate_skills": False, "codex_hooks": False, "git_hook": False}

    def _generate_skills(repo_root):
        called["generate_skills"] = True
        return repo_root / ".claude" / "skills"

    def _install_codex_hooks(repo_root):
        called["codex_hooks"] = True
        return Path("/tmp/fake-codex-hooks.json")

    def _install_git_hook(repo_root):
        called["git_hook"] = True
        return repo_root / ".git" / "hooks" / "pre-commit"

    monkeypatch.setattr("graph_engine.skills.generate_skills", _generate_skills)
    monkeypatch.setattr("graph_engine.skills.install_codex_hooks", _install_codex_hooks)
    monkeypatch.setattr("graph_engine.skills.install_git_hook", _install_git_hook)

    _handle_install(_args(tmp_path, "codex"))
    out = capsys.readouterr().out

    assert called["generate_skills"] is False
    assert called["codex_hooks"] is True
    assert called["git_hook"] is False  # git hooks belong to ``init``, not ``install``
    assert "Installed Codex hooks" in out


def test_handle_install_cursor_installs_cursor_hooks(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        "graph_engine.skills.install_platform_configs",
        lambda repo_root, target, dry_run=False, user_scope=False: ["Cursor"],
    )
    monkeypatch.setitem(
        __import__("graph_engine.skills", fromlist=["PLATFORMS"]).PLATFORMS,
        "cursor",
        {
            **__import__("graph_engine.skills", fromlist=["PLATFORMS"]).PLATFORMS["cursor"],
            "detect": lambda: True,
        },
    )

    called = {"cursor_hooks": False}

    def _install_cursor_hooks():
        called["cursor_hooks"] = True
        return Path("/tmp/fake-cursor-hooks.json")

    monkeypatch.setattr("graph_engine.skills.install_cursor_hooks", _install_cursor_hooks)

    _handle_install(_args(tmp_path, "cursor"))
    out = capsys.readouterr().out

    assert called["cursor_hooks"] is True
    assert "Installed Cursor hooks" in out


def test_handle_install_codebuddy_installs_only_codebuddy_native_files(
    monkeypatch, tmp_path, capsys
):
    import graph_engine.skills as skills_module

    assert "codebuddy" in __import__(
        "reviewgraph.cli", fromlist=["_PLATFORM_CHOICES"]
    )._PLATFORM_CHOICES

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        "graph_engine.skills.install_platform_configs",
        lambda repo_root, target, dry_run=False, user_scope=False: ["CodeBuddy Code"],
    )

    called = {
        "claude_skills": False,
        "codebuddy_skills": False,
        "codebuddy_hooks": False,
        "codebuddy_instructions": False,
    }

    def _generate_skills(repo_root):
        called["claude_skills"] = True
        return repo_root / ".claude" / "skills"

    def _install_codebuddy_skills(repo_root):
        called["codebuddy_skills"] = True
        return repo_root / ".codebuddy" / "skills"

    def _install_codebuddy_hooks(repo_root):
        called["codebuddy_hooks"] = True
        return repo_root / ".codebuddy" / "settings.json"

    def _inject_instruction_files(
        repo_root, target="all", *, include_claude_md=True, user_scope=False
    ):
        called["codebuddy_instructions"] = target == "codebuddy"
        return {"CODEBUDDY.md": "created"}

    monkeypatch.setattr(skills_module, "generate_skills", _generate_skills)
    monkeypatch.setattr(
        skills_module,
        "install_codebuddy_skills",
        _install_codebuddy_skills,
        raising=False,
    )
    monkeypatch.setattr(
        skills_module,
        "install_codebuddy_hooks",
        _install_codebuddy_hooks,
        raising=False,
    )
    monkeypatch.setattr(
        skills_module,
        "inject_instruction_files",
        _inject_instruction_files,
    )

    args = _args(tmp_path, "codebuddy")
    args.no_instructions = False
    _handle_install(args)
    out = capsys.readouterr().out

    assert called == {
        "claude_skills": False,
        "codebuddy_skills": True,
        "codebuddy_hooks": True,
        "codebuddy_instructions": True,
    }
    assert "Installed CodeBuddy skills" in out
    assert "Installed CodeBuddy hooks" in out


# --- RFC 0004: install is user-level, init seeds the repository -----------------


def _run_cli(monkeypatch, *argv: str) -> None:
    import sys

    from reviewgraph import cli

    monkeypatch.setattr(sys, "argv", ["reviewgraph", *argv])
    cli.main()


def test_install_writes_user_level_files_only(monkeypatch, tmp_path):
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setenv("HERMES_HOME", str(home / ".hermes"))
    monkeypatch.chdir(work)

    _run_cli(monkeypatch, "install", "-y")

    assert list(work.iterdir()) == []  # nothing under the working directory
    assert (home / ".claude.json").exists()
    assert (home / ".claude" / "CLAUDE.md").exists()
    assert "reviewgraph" in json.loads((home / ".claude.json").read_text())["mcpServers"]
    # A user-level entry must not pin one repository.
    entry = json.loads((home / ".claude.json").read_text())["mcpServers"]["reviewgraph"]
    assert "cwd" not in entry


def test_install_inside_a_repo_leaves_the_repo_untouched(monkeypatch, tmp_path):
    import subprocess

    home = tmp_path / "home"
    home.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setenv("HERMES_HOME", str(home / ".hermes"))
    monkeypatch.chdir(repo)

    _run_cli(monkeypatch, "install", "-y")

    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, check=True
    )
    assert status.stdout == ""


def test_init_seeds_the_repo_and_installs_nothing_for_agents(monkeypatch, tmp_path):
    import subprocess

    home = tmp_path / "home"
    home.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.chdir(repo)

    _run_cli(monkeypatch, "init")

    assert (repo / ".reviewgraph" / "graph.db").exists()
    assert ".reviewgraph/" in (repo / ".gitignore").read_text()
    assert (repo / ".git" / "hooks" / "pre-commit").exists()
    for agent_file in (
        ".mcp.json", ".cursor", ".claude", ".gemini", ".kiro", ".qoder", ".vscode",
        "CLAUDE.md", "AGENTS.md", "GEMINI.md",
    ):
        assert not (repo / agent_file).exists(), agent_file
    assert list(home.iterdir()) == []


def test_init_no_build_seeds_without_a_graph(monkeypatch, tmp_path):
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    monkeypatch.chdir(repo)

    _run_cli(monkeypatch, "init", "--no-build")

    assert ".reviewgraph/" in (repo / ".gitignore").read_text()
    assert not (repo / ".reviewgraph" / "graph.db").exists()


def test_init_dry_run_writes_nothing(monkeypatch, tmp_path, capsys):
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    monkeypatch.chdir(repo)

    _run_cli(monkeypatch, "init", "--dry-run")

    assert "[dry-run]" in capsys.readouterr().out
    assert not (repo / ".reviewgraph").exists()
    assert not (repo / ".gitignore").exists()


def test_uninstall_removes_the_user_level_entries_install_wrote(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    repo = tmp_path / "repo"
    (repo / ".git" / "hooks").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setenv("HERMES_HOME", str(home / ".hermes"))
    monkeypatch.chdir(repo)
    _run_cli(monkeypatch, "install", "-y")

    report = uninstall.run(repo=repo, keep_data=True)

    assert report.errors == []
    assert "reviewgraph" not in json.loads((home / ".claude.json").read_text()).get(
        "mcpServers", {}
    )
    assert not (home / ".claude" / "CLAUDE.md").exists()
    assert not (home / ".claude" / "skills" / "review-changes" / "SKILL.md").exists()
