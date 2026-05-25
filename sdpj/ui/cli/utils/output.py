"""CLI 输出格式化工具 — Rich 渲染"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.text import Text

_console = Console()


def success(msg: str) -> None:
    _console.print(Text(f"✓ {msg}", style="bold green"))


def error(msg: str) -> None:
    _console.print(Text(f"✗ {msg}", style="bold red"))


def info(msg: str) -> None:
    _console.print(Text(f"  {msg}", style="dim"))


def table(headers: list[str], rows: list[list[str]]) -> None:
    if not rows:
        _console.print(Text("  (无数据)", style="dim"))
        return
    rt = RichTable(border_style="dim blue")
    for h in headers:
        rt.add_column(h, style="cyan")
    for row in rows:
        rt.add_row(*[str(c) for c in row])
    _console.print(rt)


def kv(data: dict, indent: int = 2) -> None:
    lines = []
    for k, v in data.items():
        k_text = Text(f"{k}: ", style="bold cyan")
        v_text = Text(str(v))
        lines.append(Text.assemble((indent * " "), k_text, v_text))
    for line in lines:
        _console.print(line)
