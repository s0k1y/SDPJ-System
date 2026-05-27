"""CLI 主入口.

职责 16-18: 命令提示与帮助,本地终端用户会话,接口契约.
仅依赖 StateSchedulerInterface,不含业务逻辑.
"""

import asyncio
import atexit
from datetime import datetime
from pathlib import Path

import click

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.cli import BANNER, OrderedGroup
from sdpj.ui.cli.commands.adapter import config_group
from sdpj.ui.cli.commands.detect import detect_group
from sdpj.ui.cli.commands.report import report_group
from sdpj.ui.cli.commands.user import user_group
from sdpj.ui.cli.session import load_session


class CLIContext:
    """本地终端用户会话上下文 (职责 17)."""

    def __init__(self, scheduler: StateSchedulerInterface | None) -> None:  # noqa: D107
        self.scheduler = scheduler
        self.current_user_id: int | None = load_session()

    def require_login(self) -> int:  # noqa: D102
        if self.current_user_id is None:
            msg = "请先登录 (sdpj User login)"
            raise click.ClickException(msg)
        return self.current_user_id


def _resolve_db_path() -> Path:
    from sdpj.infrastructure.config.settings import get_settings  # noqa: PLC0415

    url = get_settings().db_url
    if "sqlite" in url:
        path_str = url.split(":///")[-1]
        return Path(path_str).resolve()
    return Path("sdpj/infrastructure/database/sdpj.db").resolve()


def _cleanup(scheduler: StateSchedulerInterface) -> None:
    pass


def _bootstrap() -> StateSchedulerInterface:
    from sdpj.bootstrap import build_scheduler  # noqa: PLC0415

    return build_scheduler()


def _page_output(text: str) -> None:
    """内置分页输出,跨平台通用.Space/Enter 下一页,b 上一页,q 退出.."""
    import shutil  # noqa: PLC0415

    term_size = shutil.get_terminal_size(fallback=(80, 24))
    page_height = max(term_size.lines - 1, 1)
    lines = text.split("\n")
    total = len(lines)
    offset = 0

    while True:
        chunk = lines[offset : offset + page_height]
        click.echo("\n".join(chunk))
        if offset + page_height >= total:
            break
        current = min(offset + page_height, total)
        click.echo(
            click.style(
                f"\n—— {current}/{total} (Space/Enter 下一页,b 上一页,q 退出) ——",
                fg="bright_black",
            ),
        )
        try:
            key = click.getchar()
        except (KeyboardInterrupt, EOFError):
            break
        if key in ("q", "Q"):
            break
        if key in ("b", "B"):
            offset = max(0, offset - page_height)
        else:
            offset += page_height


# ── system 子命令组 ──


@click.group("System", cls=OrderedGroup, no_args_is_help=True)
def system_group() -> None:
    """系统监控与管理."""


@system_group.command("logs")
@click.option("--category", default=None, type=click.Choice(["operation", "runtime", "error"]))
@click.option("--module", "source_module", default=None, help="来源模块")
@click.option("--user-id", default=None, help="用户ID")
@click.option("--page", default=None, type=int, help="页码")
@click.option("--page-size", default=None, type=int, help="每页条数")
@click.pass_context
def system_logs(ctx, category, source_module, user_id, page, page_size) -> None:  # noqa: ANN001, C901, PLR0913
    """查询系统日志."""
    import asyncio  # noqa: PLC0415

    from sdpj.ui.cli.utils import output  # noqa: PLC0415

    filters = {}
    if category:
        filters["category"] = category
    if source_module:
        filters["source_module"] = source_module
    if user_id:
        try:
            filters["user_id"] = int(user_id)
        except (ValueError, TypeError):
            output.error(f"--user-id 必须为整数,收到: {user_id},示例: --user-id 1")
            return
    if page is not None:
        filters["page"] = page
    if page_size is not None:
        filters["page_size"] = page_size
    entries = asyncio.run(ctx.obj.scheduler.query_logs(filters or None))
    logs_list = entries.get("logs", []) if isinstance(entries, dict) else entries
    total = entries.get("total", len(logs_list)) if isinstance(entries, dict) else len(logs_list)
    if not logs_list:
        output.info("暂无日志")
        return

    lines = []
    if total != len(logs_list):
        lines.append(f"共 {total} 条,当前显示 {len(logs_list)} 条")
    for e in logs_list:
        ts_val = e.get("timestamp", "") if isinstance(e, dict) else getattr(e, "timestamp", "")
        if isinstance(ts_val, datetime):
            ts = ts_val.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts = str(ts_val)
        cat = e.get("category", "") if isinstance(e, dict) else getattr(e, "category", "")
        desc = (
            e.get("description", str(e))
            if isinstance(e, dict)
            else getattr(e, "description", str(e))
        )
        lines.append(f"  [{ts}] [{cat}] {desc}")
    _page_output("\n".join(lines))


# ── 主 Group ──


@click.group(
    cls=OrderedGroup,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option("SDPJ-System V1.0.0", "-v", "--version", message="%(version)s")
@click.pass_context
def cli(ctx) -> None:  # noqa: ANN001, D103
    ctx.ensure_object(dict)
    if isinstance(ctx.obj, CLIContext):
        return

    try:
        scheduler = _bootstrap()
    except Exception as e:  # noqa: BLE001
        scheduler = None
        click.echo(click.style(f"[ERR] 系统初始化失败: {e}", fg="red"), err=True)
        click.echo("请检查数据库连接配置.", err=True)

    if scheduler is not None:
        try:
            db_path = _resolve_db_path()
            is_new_db = not db_path.exists()
            if is_new_db:
                click.echo(click.style("[Init] 数据库不存在,正在初始化...", fg="yellow"), err=True)
                asyncio.run(scheduler.startup())
                click.echo(click.style("[Init] 数据库初始化完成", fg="green"), err=True)
            else:
                asyncio.run(scheduler.session_init())
        except Exception as e:  # noqa: BLE001
            click.echo(click.style(f"[Init] 系统初始化失败: {e}", fg="red"), err=True)

        atexit.register(_cleanup, scheduler)
    ctx.obj = CLIContext(scheduler)


# 按逻辑顺序注册
cli.add_command(user_group)
cli.add_command(config_group)
cli.add_command(detect_group)
cli.add_command(report_group)
cli.add_command(system_group)

cli._banner = BANNER  # noqa: SLF001
cli._groups = None  # noqa: SLF001
