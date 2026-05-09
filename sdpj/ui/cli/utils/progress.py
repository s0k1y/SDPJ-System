"""CLI 进度条显示工具"""

import click


def show_progress(items: list, label: str = "处理中") -> None:
    with click.progressbar(items, label=label) as bar:
        for item in bar:
            yield item


def spinner(msg: str) -> None:
    click.echo(f"  {msg} ...")
