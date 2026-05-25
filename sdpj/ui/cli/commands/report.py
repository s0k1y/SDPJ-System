"""报告交互命令 (职责 4-7)"""

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from sdpj.ui.cli import OrderedGroup
from sdpj.ui.cli.schemas.report import ReportExportParams
from sdpj.ui.cli.utils import output
from sdpj.ui.cli.utils.result import unwrap

_console = Console()


# ── Rich 渲染辅助函数 ──


def _bar(ratio: float, width: int = 28) -> str:
    if ratio <= 0:
        return " " * width
    filled = max(1, round(ratio * width / 100))
    return "█" * filled + " " * (width - filled)


def _render_visualization(data: dict, *, group_id: str = "") -> None:
    color_map = {"通过": "green", "合规": "green", "失败": "red", "违规": "red"}
    _console.print()

    # ── 摘要面板 ──
    overall = data.get("overall_rate", 0)
    asr = data.get("attack_success_rate", 0)
    stats = data.get("statistics", {})
    risk = stats.get("risk_level", data.get("statistics", {}).get("risk_level", "?"))

    risk_color = "red" if "高" in str(risk) else "yellow" if "中" in str(risk) else "green"
    summary = Text()
    summary.append(f"任务组: {group_id[:12]}\n", style="bold cyan")
    summary.append(f"合规率: {overall:.1f}%", style="bold green")
    summary.append(f"    攻击成功率: {asr:.1f}%", style="bold red")
    summary.append(f"    风险等级: {risk}", style=f"bold {risk_color}")
    if stats:
        summary.append(f"\n检测 {stats.get('total', 0)} 条  |  ")
        summary.append(f"通过 {stats.get('compliant', 0)} 条", style="green")
        summary.append(f"  |  ")
        summary.append(f"未通过 {stats.get('non_compliant', 0)} 条", style="red")
    _console.print(Panel(summary, title="[bold]检测报告摘要[/bold]", border_style="cyan", width=60))

    # ── 合规率条形图 ──
    compliance_ratio = data.get("compliance_ratio", {}).get("data", [])
    if compliance_ratio:
        _console.print("\n[bold]合规占比[/bold]")
        for item in compliance_ratio:
            name = item.get("name", "?")
            value = item.get("value", 0)
            color = color_map.get(name, "white")
            pct = value / stats.get("total", 1) * 100
            _console.print(f"  {name:<6} [{color}]{_bar(pct)}[/{color}] {pct:.1f}% ({value})")

    # ── 风险分布条形图 ──
    risk_dist = data.get("risk_distribution", {}).get("data", [])
    if risk_dist:
        _console.print("\n[bold]风险类别分布[/bold]")
        for item in risk_dist:
            name = item.get("name", "?")
            value = item.get("value", 0)
            pct = value / max(1, stats.get("total", 1)) * 100
            _console.print(f"  {name:<12} [red]{_bar(pct)}[/red] {pct:.1f}% ({value})")

    # ── 子类别合规明细表格 ──
    subtype = data.get("subtype_compliance", [])
    if subtype:
        _console.print()
        table = Table(title="子类别合规明细", border_style="dim blue")
        table.add_column("类别", style="cyan")
        table.add_column("总数", justify="right")
        table.add_column("通过", justify="right", style="green")
        table.add_column("失败", justify="right", style="red")
        table.add_column("合规率", justify="right")
        for item in subtype:
            passed = item.get("passed", 0)
            failed = item.get("failed", 0)
            rate = item.get("rate", 0)
            rate_color = "green" if rate >= 70 else "yellow" if rate >= 40 else "red"
            table.add_row(
                str(item.get("category", "?")),
                str(item.get("total", 0)),
                str(passed),
                str(failed),
                f"[{rate_color}]{rate:.1f}%[/{rate_color}]",
            )
        _console.print(table)

    # ── 数据集对比表格 ──
    dataset_comp = data.get("dataset_comparison", {}).get("data", [])
    if dataset_comp:
        _console.print()
        table = Table(title="数据集对比", border_style="dim blue")
        table.add_column("数据集ID", style="cyan")
        table.add_column("检测数", justify="right")
        table.add_column("合规率", justify="right")
        table.add_column("风险等级")
        for item in dataset_comp:
            ds_id = str(item.get("dataset_id", "?"))
            total = item.get("total", 0)
            rate = item.get("compliance_rate", 0)
            risk_lvl = item.get("risk_level", "?")
            risk_lvl_color = "red" if "高" in str(risk_lvl) else "yellow" if "中" in str(risk_lvl) else "green"
            rate_color = "green" if rate >= 70 else "yellow" if rate >= 40 else "red"
            table.add_row(
                ds_id,
                str(total),
                f"[{rate_color}]{rate:.1f}%[/{rate_color}]",
                f"[{risk_lvl_color}]{risk_lvl}[/{risk_lvl_color}]",
            )
        _console.print(table)

    _console.print()


@click.group("Report", cls=OrderedGroup, no_args_is_help=True)
def report_group():
    """检测报告管理"""


# ── 报告生成与查看 ──


@report_group.command("generate", hidden=True)
@click.option("--group-id", required=True, help="任务组ID")
@click.pass_context
def generate(ctx, group_id):
    """生成检测报告"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.generate_report(group_id, user_id=user_id)
    )
    data = unwrap(result, required="report")
    output.success("报告已生成")
    output.kv(data["report"])


@report_group.command("view")
@click.option("--group-id", required=True, help="任务组ID")
@click.pass_context
def view(ctx, group_id):
    """查看单份检测报告"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.view_report(group_id, user_id=user_id))
    data = unwrap(result, required="report")
    output.kv(data["report"])


@report_group.command("list")
@click.option("--model-id", default=None, help="按模型ID过滤")
@click.pass_context
def list_reports(ctx, model_id):
    """查询检测报告列表"""
    user_id = ctx.obj.require_login()
    filters = {"user_id": user_id}
    if model_id:
        filters["model_id"] = model_id
    reports = asyncio.run(ctx.obj.scheduler.list_reports(filters))
    if not reports:
        output.info("暂无报告")
        return
    rows = [
        [str(r.get("task_group_id", "")), r.get("model_id", ""), r.get("status", "")]
        for r in reports
    ]
    output.table(["任务组ID", "模型", "状态"], rows)


# ── 报告导出与删除 ──


@report_group.command("export")
@click.option("--group-id", required=True, help="任务组ID")
@click.option(
    "--format",
    "target_format",
    default="json",
    type=click.Choice(["json", "yaml", "jsonl"]),
    help="导出格式",
)
@click.option("--task-id", default=None, help="子任务ID（导出单任务级别报告）")
@click.option("--output", "output_path", default=None, help="输出文件路径")
@click.pass_context
def export(ctx, group_id, target_format, task_id, output_path):
    """导出检测报告文件"""
    user_id = ctx.obj.require_login()
    params = ReportExportParams(
        task_group_id=group_id, target_format=target_format, task_id=task_id
    )
    result = asyncio.run(
        ctx.obj.scheduler.export_report(
            params.task_group_id, params.target_format, user_id=user_id, task_id=params.task_id
        )
    )
    data = unwrap(result)
    filename = data.get("filename", f"report.{target_format}")
    content = data.get("content", "")
    if output_path:
        target = Path(output_path)
        if target.is_dir():
            target = target / filename
        target.write_text(content, encoding="utf-8")
        output.success(f"已导出至 {target}")
    else:
        Path(filename).write_text(content, encoding="utf-8")
        output.success(f"已导出至 {filename}")


@report_group.command("delete")
@click.option("--target-id", required=True, help="目标ID")
@click.option(
    "--granularity",
    default="task_group",
    type=click.Choice(["task_group", "task"]),
    help="删除粒度: task_group=任务组, task=子任务",
)
@click.pass_context
def delete(ctx, target_id, granularity):
    """删除检测报告"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.delete_report(target_id, user_id, granularity))
    unwrap(result)
    output.success("已删除")


# ── 统计分析 ──


@report_group.command("statistics")
@click.pass_context
def statistics(ctx):
    """查询合规统计数据"""
    result = asyncio.run(ctx.obj.scheduler.query_compliance_statistics())
    data = unwrap(result)
    if not data:
        output.info("暂无统计数据")
        return
    output.kv(data)


@report_group.command("visualization")
@click.option("--group-id", default=None, help="任务组ID")
@click.option("--task-id", default=None, help="任务ID")
@click.pass_context
def visualization(ctx, group_id, task_id):
    """获取可视化数据"""
    if not group_id and not task_id:
        raise click.UsageError("必须指定 --group-id 或 --task-id")
    user_id = ctx.obj.require_login()
    if group_id:
        result = asyncio.run(ctx.obj.scheduler.prepare_visualization_data(group_id, user_id=user_id))
        label = group_id
    else:
        result = asyncio.run(ctx.obj.scheduler.prepare_task_visualization_data(task_id, user_id=user_id))
        label = task_id
    data = unwrap(result, required="data")
    _render_visualization(data["data"], group_id=label)
