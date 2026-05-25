"""CLI 进度条显示工具 — Rich 渲染"""

from contextlib import contextmanager

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

_console = Console()


@contextmanager
def spinner(msg: str):
    progress = Progress(
        SpinnerColumn(),
        TextColumn(f"[bold cyan]{msg}[/bold cyan]"),
        transient=True,
        console=_console,
    )
    progress.start()
    try:
        yield
    finally:
        progress.stop()


def show_progress(items: list, label: str = "处理中"):
    progress = Progress(
        TextColumn(f"[bold]{label}[/bold]"),
        BarColumn(),
        TaskProgressColumn(),
        transient=True,
        console=_console,
    )
    task_id = progress.add_task(label, total=len(items))
    progress.start()
    try:
        for item in items:
            yield item
            progress.advance(task_id)
    finally:
        progress.stop()
