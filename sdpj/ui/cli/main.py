"""CLI 主入口

职责 16-18: 命令提示与帮助、本地终端用户会话、接口契约。
仅依赖 StateSchedulerInterface，不含业务逻辑。
"""
import click

from sdpj.control.state_scheduler_interface import StateSchedulerInterface


class CLIContext:
    """本地终端用户会话上下文 (职责 17)"""

    def __init__(self, scheduler: StateSchedulerInterface) -> None:
        self.scheduler = scheduler
        self.current_user_id: int | None = None

    def require_login(self) -> int:
        if self.current_user_id is None:
            raise click.ClickException("请先登录 (sdpj user login)")
        return self.current_user_id


def _bootstrap() -> StateSchedulerInterface:
    from sdpj.bootstrap import build_scheduler
    return build_scheduler()


@click.group()
@click.pass_context
def cli(ctx):
    """SDPJ-System 命令行工具"""
    try:
        scheduler = _bootstrap()
    except Exception as e:
        scheduler = None
        click.echo(click.style(f"[WARN] 系统初始化失败: {e}", fg="yellow"), err=True)
        click.echo("部分命令可能不可用。", err=True)

    ctx.ensure_object(dict)
    ctx.obj = CLIContext(scheduler)


from sdpj.ui.cli.commands.detect import detect_group
from sdpj.ui.cli.commands.report import report_group
from sdpj.ui.cli.commands.user import user_group
from sdpj.ui.cli.commands.adapter import config_group

cli.add_command(detect_group)
cli.add_command(report_group)
cli.add_command(user_group)
cli.add_command(config_group)


@cli.command("watch")
@click.option("--interval", default=2, help="轮询间隔秒数")
@click.pass_context
def watch(ctx, interval):
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
        ctx.obj.scheduler.unsubscribe_state_changes(on_state_change)
        click.echo("已停止监听")


@cli.command("watch-errors")
@click.pass_context
def watch_errors(ctx):
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
        ctx.obj.scheduler.unsubscribe_errors(on_error)
        click.echo("已停止监听")


@cli.command("status")
@click.pass_context
def status(ctx):
    """查询系统状态 (职责 8)"""
    from sdpj.ui.cli.utils import output
    state = ctx.obj.scheduler.get_system_state()
    output.info(f"系统状态: {state}")


@cli.command("logs")
@click.option("--category", default=None, type=click.Choice(["operation", "runtime", "error"]))
@click.option("--module", "source_module", default=None, help="来源模块")
@click.option("--user-id", default=None, help="用户ID")
@click.pass_context
def logs(ctx, category, source_module, user_id):
    """查询系统日志 (职责 9)"""
    import asyncio
    from sdpj.ui.cli.utils import output
    filters = {}
    if category:
        filters["category"] = category
    if source_module:
        filters["source_module"] = source_module
    if user_id:
        filters["user_id"] = user_id
    entries = asyncio.run(ctx.obj.scheduler.query_logs(filters or None))
    if not entries:
        output.info("暂无日志")
        return
    for e in entries:
        ts = getattr(e, "timestamp", "")
        cat = getattr(e, "category", "")
        desc = getattr(e, "description", str(e))
        click.echo(f"  [{ts}] [{cat}] {desc}")
