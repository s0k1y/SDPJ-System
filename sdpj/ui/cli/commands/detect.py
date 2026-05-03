"""检测交互命令 (职责 1-3)"""
import asyncio
import click

from sdpj.ui.cli.utils import output


@click.group("detect")
def detect_group():
    """检测任务管理"""
    pass


@detect_group.command("start")
@click.option("--model-id", required=True, help="目标被测大模型标识")
@click.option("--type", "detection_type", default="static",
              type=click.Choice(["static", "dynamic"]), help="检测类型")
@click.option("--dataset", "dataset_ids", multiple=True, type=int, help="检测数据集ID (可多选)")
@click.option("--config-id", type=int, default=None, help="私有检测配置标识")
@click.option("--max-iter", default=3, type=int, help="动态算法最大迭代次数")
@click.pass_context
def start(ctx, model_id, detection_type, dataset_ids, config_id, max_iter):
    """启动检测任务"""
    cli_ctx = ctx.obj
    user_id = cli_ctx.require_login()
    scheduler = cli_ctx.scheduler

    config_data = {
        "model_id": model_id,
        "detection_type": detection_type,
        "dataset_ids": list(dataset_ids),
        "max_iterations": max_iter,
    }
    if config_id is not None:
        config_data["config_id"] = config_id

    result = asyncio.run(scheduler.start_detection(user_id, config_data))
    if result["success"]:
        output.success(f"任务组 {result['task_group_id']} 已创建")
        for tid in result.get("task_ids", []):
            output.info(f"子任务: {tid}")
    else:
        output.error(result.get("error", "启动失败"))


@detect_group.command("datasets")
@click.pass_context
def datasets(ctx):
    """查询可用检测数据集清单"""
    scheduler = ctx.obj.scheduler
    ds_list = asyncio.run(scheduler.query_available_datasets())
    if not ds_list:
        output.info("暂无可用数据集")
        return
    rows = [[str(d.get("id", "")), d.get("name", ""), d.get("risk_type", "")] for d in ds_list]
    output.table(["ID", "名称", "风险类型"], rows)


@detect_group.command("progress")
@click.option("--task-id", default=None, help="队列任务标识 (省略则查询整体视图)")
@click.pass_context
def progress(ctx, task_id):
    """查询检测任务执行进度"""
    scheduler = ctx.obj.scheduler
    result = asyncio.run(scheduler.query_detection_progress(task_id))
    if not result.get("success"):
        output.error(result.get("error", "查询失败"))
        return
    if task_id:
        output.info(f"任务 {task_id}: {result['status']}")
    else:
        queue = result.get("queue", [])
        rows = [[q["task_id"][:8], q["status"]] for q in queue]
        output.table(["任务ID", "状态"], rows)


@detect_group.command("run")
@click.option("--concurrency", default=3, type=int, help="并发度上限")
@click.pass_context
def run_tasks(ctx, concurrency):
    """并发执行队列中的检测子任务"""
    scheduler = ctx.obj.scheduler
    result = asyncio.run(scheduler.execute_concurrent_tasks(concurrency))
    if result.get("message"):
        output.info(result["message"])
    for t in result.get("tasks", []):
        status = "OK" if t.get("success") else "FAIL"
        output.info(f"  {t.get('task_id', '?')[:8]}: {status}")
