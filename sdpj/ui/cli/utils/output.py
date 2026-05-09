"""CLI 输出格式化工具"""

import click


def success(msg: str) -> None:
    click.echo(click.style(f"[OK] {msg}", fg="green"))


def error(msg: str) -> None:
    click.echo(click.style(f"[ERR] {msg}", fg="red"), err=True)


def info(msg: str) -> None:
    click.echo(f"  {msg}")


def table(headers: list[str], rows: list[list[str]]) -> None:
    if not rows:
        click.echo("  (无数据)")
        return
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    click.echo(fmt.format(*headers))
    click.echo("  ".join("-" * w for w in widths))
    for row in rows:
        padded = [str(row[i]) if i < len(row) else "" for i in range(len(headers))]
        click.echo(fmt.format(*padded))


def kv(data: dict, indent: int = 2) -> None:
    prefix = " " * indent
    for k, v in data.items():
        click.echo(f"{prefix}{k}: {v}")
