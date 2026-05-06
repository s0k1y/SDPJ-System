"""报告交互命令 (职责 4-7)"""
import asyncio
import click

from sdpj.ui.cli.utils import output


@click.group("report")
def report_group():
    """检测报告管理"""
    pass


@report_group.command("generate")
@click.argument("task_group_id")
@click.option("--type", "detection_type", default="static",
              type=click.Choice(["static", "dynamic"]), help="检测类型")
@click.pass_context
def generate(ctx, task_group_id, detection_type):
    """生成检测报告"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.generate_report(task_group_id, detection_type, user_id=user_id))
    if result["success"]:
        output.success("报告已生成")
        output.kv(result.get("report", {}))
    else:
        output.error(result.get("error", "生成失败"))


@report_group.command("view")
@click.argument("task_group_id")
@click.pass_context
def view(ctx, task_group_id):
    """查看单份检测报告"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.view_report(task_group_id, user_id=user_id))
    report = result.get("report", {})
    if not report:
        output.info("报告不存在")
        return
    output.kv(report)


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


@report_group.command("delete")
@click.argument("target_id")
@click.option("--granularity", default="task_group",
              type=click.Choice(["task_group", "task", "report", "result_data"]))
@click.pass_context
def delete(ctx, target_id, granularity):
    """删除检测报告"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.delete_report(target_id, user_id, granularity))
    if result["success"]:
        output.success("已删除")
    else:
        output.error(result.get("error", result.get("message", "删除失败")))


@report_group.command("export")
@click.argument("task_group_id")
@click.option("--format", "target_format", default="json",
              type=click.Choice(["json", "yaml", "jsonl"]), help="导出格式")
@click.option("--output", "output_path", default=None, help="输出文件路径")
@click.pass_context
def export(ctx, task_group_id, target_format, output_path):
    """导出检测报告文件"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.export_report(task_group_id, target_format, user_id=user_id))
    if not result["success"]:
        output.error(result.get("error", "导出失败"))
        return
    filename = result.get("filename", f"report.{target_format}")
    content = result.get("content", "")
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        output.success(f"已导出至 {output_path}")
    else:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        output.success(f"已导出至 {filename}")


@report_group.command("statistics")
@click.pass_context
def statistics(ctx):
    """查询合规统计数据"""
    result = asyncio.run(ctx.obj.scheduler.query_compliance_statistics())
    if not result:
        output.info("暂无统计数据")
        return
    output.kv(result)


@report_group.command("visualization")
@click.argument("task_group_id")
@click.pass_context
def visualization(ctx, task_group_id):
    """获取任务组可视化数据"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.prepare_visualization_data(task_group_id, user_id=user_id))
    if not result or not result.get("success", True):
        output.error(result.get("error", "获取失败") if result else "获取失败")
        return
    output.kv(result)


@report_group.command("task-visualization")
@click.argument("task_id")
@click.pass_context
def task_visualization(ctx, task_id):
    """获取单个任务的可视化数据"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.prepare_task_visualization_data(task_id, user_id=user_id))
    if not result or not result.get("success", True):
        output.error(result.get("error", "获取失败") if result else "获取失败")
        return
    output.kv(result)
