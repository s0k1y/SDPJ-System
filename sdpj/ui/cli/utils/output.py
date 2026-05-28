"""CLI 输出格式化工具 — Rich 渲染."""

from rich.console import Console
from rich.table import Table as RichTable
from rich.text import Text

_console = Console()

_STATUS_COLORS = {
    "合规": "bold green",
    "违规": "bold red",
}


def colorize(text: str) -> Text:
    style = _STATUS_COLORS.get(text)
    if style:
        return Text(text, style=style)
    return Text(text)


def success(msg: str) -> None:  # noqa: D103
    _console.print(Text(f"✓ {msg}", style="bold green"))


def error(msg: str) -> None:  # noqa: D103
    _console.print(Text(f"✗ {msg}", style="bold red"))


def info(msg: str) -> None:  # noqa: D103
    _console.print(Text(f"  {msg}", style="dim"))


def table(headers: list[str], rows: list[list[str]]) -> None:  # noqa: D103
    if not rows:
        _console.print(Text("  (无数据)", style="dim"))
        return
    rt = RichTable(border_style="dim blue")
    for h in headers:
        rt.add_column(h, style="cyan")
    for row in rows:
        rt.add_row(*[colorize(str(c)) for c in row])
    _console.print(rt)


def kv(data: dict, indent: int = 2) -> None:  # noqa: D103
    lines = []
    for k, v in data.items():
        k_text = Text(f"{k}: ", style="bold cyan")
        v_text = colorize(str(v))
        lines.append(Text.assemble((indent * " "), k_text, v_text))
    for line in lines:
        _console.print(line)
