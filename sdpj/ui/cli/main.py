"""CLI 主入口

职责 16-18: 命令提示与帮助、本地终端用户会话、接口契约。
仅依赖 StateSchedulerInterface，不含业务逻辑。
"""

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
    """本地终端用户会话上下文 (职责 17)"""

    def __init__(self, scheduler: StateSchedulerInterface) -> None:
        self.scheduler = scheduler
        self.current_user_id: int | None = load_session()

    def require_login(self) -> int:
        if self.current_user_id is None:
            raise click.ClickException("请先登录 (sdpj User login)")
        return self.current_user_id


def _resolve_db_path() -> Path:
    from sdpj.infrastructure.config.settings import get_settings

    url = get_settings().db_url
    if "sqlite" in url:
        path_str = url.split(":///")[-1]
        return Path(path_str).resolve()
    return Path("sdpj/infrastructure/database/sdpj.db").resolve()


def _bootstrap() -> StateSchedulerInterface:
    from sdpj.bootstrap import build_scheduler

    return build_scheduler()


def _page_output(text: str) -> None:
    """内置分页输出，跨平台通用。Space/Enter 下一页，b 上一页，q 退出。"""
    import shutil

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
                f"\n—— {current}/{total} (Space/Enter 下一页，b 上一页，q 退出) ——",
                fg="bright_black",
            )
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
def system_group():
    """系统监控与管理"""


@system_group.command("status")
@click.pass_context
def system_status(ctx):
    """查询系统状态"""
    from sdpj.ui.cli.utils import output

    state = ctx.obj.scheduler.get_system_state()
    output.info(f"系统状态: {state}")


@system_group.command("logs")
@click.option("--category", default=None, type=click.Choice(["operation", "runtime", "error"]))
@click.option("--module", "source_module", default=None, help="来源模块")
@click.option("--user-id", default=None, help="用户ID")
@click.option("--page", default=None, type=int, help="页码")
@click.option("--page-size", default=None, type=int, help="每页条数")
@click.pass_context
def system_logs(ctx, category, source_module, user_id, page, page_size):
    """查询系统日志"""
    import asyncio

    from sdpj.ui.cli.utils import output

    filters = {}
    if category:
        filters["category"] = category
    if source_module:
        filters["source_module"] = source_module
    if user_id:
        try:
            filters["user_id"] = int(user_id)
        except (ValueError, TypeError):
            output.error(f"--user-id 必须为整数，收到: {user_id}，示例: --user-id 1")
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
        lines.append(f"共 {total} 条，当前显示 {len(logs_list)} 条")
    for e in logs_list:
        ts = e.get("timestamp", "") if isinstance(e, dict) else getattr(e, "timestamp", "")
        cat = e.get("category", "") if isinstance(e, dict) else getattr(e, "category", "")
        desc = (
            e.get("description", str(e))
            if isinstance(e, dict)
            else getattr(e, "description", str(e))
        )
        lines.append(f"  [{ts}] [{cat}] {desc}")
    _page_output("\n".join(lines))


@system_group.command("watch")
@click.option("--interval", default=2, help="轮询间隔秒数")
@click.pass_context
def system_watch(ctx, interval):
    """实时监听系统状态变更推送"""
    import time

    last_state = [None]

    def on_state_change(new_state: str) -> None:
        if new_state != last_state[0]:
            last_state[0] = new_state
            click.echo(f"[状态变更] {new_state}")

    ctx.obj.scheduler.subscribe_state_changes(on_state_change)
    click.echo("开始监听系统状态，按 Ctrl+C 退出...")
    try:
        while True:
            current = ctx.obj.scheduler.get_system_state()
            on_state_change(current)
            time.sleep(interval)
    except KeyboardInterrupt:
        click.echo("\n正在停止... (再次按 Ctrl+C 强制退出)")
        try:
            ctx.obj.scheduler.unsubscribe_state_changes(on_state_change)
            click.echo("已停止监听")
        except KeyboardInterrupt:
            click.echo("强制退出")


@system_group.command("watch-errors")
@click.pass_context
def system_watch_errors(ctx):
    """实时监听系统异常推送"""
    import time

    def on_error(err_type: str, desc: str) -> None:
        click.echo(click.style(f"[异常] {err_type}: {desc}", fg="red"))

    ctx.obj.scheduler.subscribe_errors(on_error)
    click.echo("开始监听系统异常，按 Ctrl+C 退出...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\n正在停止... (再次按 Ctrl+C 强制退出)")
        try:
            ctx.obj.scheduler.unsubscribe_errors(on_error)
            click.echo("已停止监听")
        except KeyboardInterrupt:
            click.echo("强制退出")


# ── 主 Group ──


@click.group(
    cls=OrderedGroup,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option("SDPJ-System V1.0.0", "-v", "--version", message="%(version)s")
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    if isinstance(ctx.obj, CLIContext):
        return

    try:
        scheduler = _bootstrap()
    except Exception as e:
        scheduler = None
        click.echo(click.style(f"[ERR] 系统初始化失败: {e}", fg="red"), err=True)
        click.echo("请检查数据库连接配置，或运行 sdpj System status 查看系统状态。", err=True)

    if scheduler is not None:
        db_path = _resolve_db_path()
        if not db_path.exists():
            click.echo(click.style("[Init] 数据库不存在，正在初始化...", fg="yellow"), err=True)
            import asyncio

            try:
                asyncio.run(scheduler.startup())
                click.echo(click.style("[Init] 数据库初始化完成", fg="green"), err=True)
            except Exception as e:
                click.echo(click.style(f"[Init] 数据库初始化失败: {e}", fg="red"), err=True)
    ctx.obj = CLIContext(scheduler)


# 按逻辑顺序注册
cli.add_command(user_group)
cli.add_command(config_group)
cli.add_command(detect_group)
cli.add_command(report_group)
cli.add_command(system_group)

cli._banner = BANNER
cli._groups = None
