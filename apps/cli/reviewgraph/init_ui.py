"""Terminal reporting for ``reviewgraph install`` and ``reviewgraph init`` (RFC 0003).

Handlers report through a reporter. ``PlainReporter`` prints exactly the lines
the commands always printed; ``RichReporter`` renders a banner, live step rows,
tables and a summary panel. ``make_reporter`` picks one: rich only on a real
terminal that wants colour.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from typing import Any


class _Step:
    """Context manager for one unit of work; ``done``/``skip`` set the outcome text."""

    def __init__(self, ui: Reporter, label: str) -> None:
        self._ui = ui
        self._label = label
        self._kind = "done"
        self._text: str | None = None

    def done(self, text: str) -> None:
        self._kind, self._text = "done", text

    def skip(self, text: str) -> None:
        self._kind, self._text = "skip", text

    def __enter__(self) -> _Step:
        self._ui._begin(self._label)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is not None:
            self._ui._end(self._label, "fail", None, str(exc) or exc_type.__name__)
        else:
            self._ui._end(self._label, self._kind, self._text, None)


class Reporter:
    """Interface shared by both reporters."""

    def start(self, title: str, plain: str | None = None, detail: str = "") -> None: ...

    def step(self, label: str) -> _Step:
        return _Step(self, label)

    def done(self, text: str) -> None: ...

    def skip(self, text: str) -> None: ...

    def would(self, text: str) -> None: ...

    def note(self, text: str) -> None: ...

    def platforms(self, names: list[str], dry_run: bool = False) -> None: ...

    def preview(self, title: str, items: list[str]) -> None: ...

    def confirm(self, prompt: str, plain_confirm: Callable[..., bool]) -> bool:
        return plain_confirm(prompt, default_yes=True)

    def finish(self, next_steps: list[str]) -> None: ...

    def _begin(self, label: str) -> None: ...

    def _end(self, label: str, kind: str, text: str | None, reason: str | None) -> None: ...


class PlainReporter(Reporter):
    """The original log output, unchanged."""

    def start(self, title: str, plain: str | None = None, detail: str = "") -> None:
        if plain is not None:
            print(plain)

    def done(self, text: str) -> None:
        print(text)

    skip = would = note = done

    def platforms(self, names: list[str], dry_run: bool = False) -> None:
        print(f"\nConfigured {len(names)} platform(s): {', '.join(names)}")

    def preview(self, title: str, items: list[str]) -> None:
        print()
        print(title)
        for item in items:
            print(f"  {item}")

    def finish(self, next_steps: list[str]) -> None:
        print()
        print("Next steps:")
        for line in next_steps:
            print(line)

    def _end(self, label: str, kind: str, text: str | None, reason: str | None) -> None:
        if kind != "fail" and text:
            print(text)


class RichReporter(Reporter):
    """Banner, live step rows, tables and a closing summary panel."""

    _MARKS = {
        "done": ("✔", "green"),
        "skip": ("–", "yellow"),
        "fail": ("✘", "bold red"),
        "would": ("◌", "cyan"),
    }

    def __init__(self, version: str) -> None:
        from rich.console import Console

        self._version = version
        self._console = Console(highlight=False)
        self._status: Any = None
        self._counts = {"done": 0, "skip": 0, "fail": 0}
        self._failures: list[tuple[str, str]] = []

    def _row(self, kind: str, text: str, reason: str | None = None) -> None:
        mark, style = self._MARKS[kind]
        line = f"[{style}]{mark}[/] {_esc(text.strip())}"
        if reason:
            line += f" [red]{_esc(reason)}[/]"
        self._console.print(line)

    def start(self, title: str, plain: str | None = None, detail: str = "") -> None:
        from rich.panel import Panel

        body = f"[bold magenta]ReviewGraph[/] [dim]{_esc(self._version)}[/]  [bold cyan]{title}[/]"
        if detail:
            body += f"\n[dim]{_esc(detail)}[/]"
        self._console.print(Panel(body, border_style="magenta", expand=False))

    def _begin(self, label: str) -> None:
        self._status = self._console.status(f"[cyan]{_esc(label)}...", spinner="dots")
        self._status.start()

    def _end(self, label: str, kind: str, text: str | None, reason: str | None) -> None:
        if self._status is not None:
            self._status.stop()
            self._status = None
        self._counts[kind] += 1
        if kind == "fail":
            self._failures.append((label, reason or ""))
        self._row(kind, text or label, reason if kind == "fail" else None)

    def done(self, text: str) -> None:
        self._counts["done"] += 1
        self._row("done", text)

    def skip(self, text: str) -> None:
        self._counts["skip"] += 1
        self._row("skip", text)

    def would(self, text: str) -> None:
        self._row("would", text)

    def note(self, text: str) -> None:
        self._console.print(f"[dim]{_esc(text.strip())}[/]")

    def platforms(self, names: list[str], dry_run: bool = False) -> None:
        from rich.table import Table

        table = Table(title=f"{len(names)} platform(s)", border_style="dim")
        table.add_column("Platform", style="bold")
        table.add_column("State")
        state = "[yellow]would configure[/]" if dry_run else "[green]configured[/]"
        for name in names:
            table.add_row(name, state)
        self._console.print(table)

    def preview(self, title: str, items: list[str]) -> None:
        from rich.table import Table

        table = Table(title=title.rstrip(":"), border_style="dim")
        table.add_column("File", style="dim")
        for item in items:
            table.add_row(item)
        self._console.print(table)

    def confirm(self, prompt: str, plain_confirm: Callable[..., bool]) -> bool:
        if not sys.stdin.isatty():
            return plain_confirm(prompt, default_yes=True)
        from rich.prompt import Confirm

        try:
            return Confirm.ask(f"[bold cyan]{_esc(prompt)}[/]", console=self._console, default=True)
        except (EOFError, KeyboardInterrupt):
            self._console.print()
            return False

    def finish(self, next_steps: list[str]) -> None:
        from rich.panel import Panel

        c = self._counts
        lines = [
            f"[green]{c['done']} done[/] · [yellow]{c['skip']} skipped[/] · "
            f"[red]{c['fail']} failed[/]"
        ]
        for label, reason in self._failures:
            lines.append(f"[red]✘ {_esc(label)}[/] [dim]{_esc(reason)}[/]")
        lines.append("")
        lines.append("[bold]Next steps[/]")
        lines.extend(_esc(line.strip()) for line in next_steps)
        border = "red" if c["fail"] else "green"
        self._console.print(Panel("\n".join(lines), title="Summary", border_style=border))


def _esc(text: str) -> str:
    from rich.markup import escape

    return escape(text)


def _wants_rich(plain: bool) -> bool:
    if plain or os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


def make_reporter(version: str, plain: bool = False) -> Reporter:
    """Rich reporter on a colour-capable terminal, otherwise the plain log."""
    if _wants_rich(plain):
        try:
            return RichReporter(version)
        except ImportError:
            pass
    return PlainReporter()
