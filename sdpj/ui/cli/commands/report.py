"""报告交互命令 (职责 4-7)"""

import asyncio

import click

from sdpj.ui.cli import OrderedGroup
from sdpj.ui.cli.schemas.report import ReportExportParams, ReportGenerateParams
from sdpj.ui.cli.utils import output
from sdpj.ui.cli.utils.result import unwrap


@click.group("Report", cls=OrderedGroup, no_args_is_help=True)
def report_group():
    """检测报告管理"""


# ── 报告生成与查看 ──


@report_group.command("generate")
@click.option("--group-id", required=True, help="任务组ID")
@click.option(
    "--type",
    "detection_type",
    default="static",
    type=click.Choice(["static", "dynamic"]),
    help="检测类型",
)
@click.pass_context
def generate(ctx, group_id, detection_type):
    """生成检测报告"""
    user_id = ctx.obj.require_login()
    params = ReportGenerateParams(task_group_id=group_id, detection_type=detection_type)
    result = asyncio.run(
        ctx.obj.scheduler.generate_report(
            params.task_group_id, params.detection_type, user_id=user_id
        )
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
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        output.success(f"已导出至 {output_path}")
    else:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        output.success(f"已导出至 {filename}")


@report_group.command("delete")
@click.option("--target-id", required=True, help="目标ID")
@click.option(
    "--granularity",
    default="task_group",
    type=click.Choice(["task_group", "task", "report", "result_data"]),
)
@click.confirmation_option(prompt="确认删除该报告?")
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
@click.option("--group-id", required=True, help="任务组ID")
@click.pass_context
def visualization(ctx, group_id):
    """获取任务组可视化数据"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.prepare_visualization_data(group_id, user_id=user_id))
    data = unwrap(result)
    output.kv(data)


@report_group.command("task-visualization")
@click.option("--task-id", required=True, help="任务ID")
@click.pass_context
def task_visualization(ctx, task_id):
    """获取单个任务的可视化数据"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.prepare_task_visualization_data(task_id, user_id=user_id)
    )
    data = unwrap(result)
    output.kv(data)
