"""检测交互命令 (职责 1-3)"""
import asyncio
import pathlib
import threading
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
@click.option("--jailbreak-dataset", "jailbreak_dataset_ids", multiple=True, type=int,
              help="用于PoC池构建的越狱数据集ID (可多选，仅 --force-refresh 时有效)")
@click.option("--config-id", type=int, default=None, help="私有检测配置标识")
@click.option("--max-iter", default=3, type=int, help="动态算法最大迭代次数")
@click.option("--force-refresh", is_flag=True, default=False, help="强制重新构建PoC池缓存")
@click.pass_context
def start(ctx, model_id, detection_type, dataset_ids, jailbreak_dataset_ids, config_id, max_iter, force_refresh):
    """启动检测任务"""
    cli_ctx = ctx.obj
    user_id = cli_ctx.require_login()
    scheduler = cli_ctx.scheduler

    config_data = {
        "model_id": model_id,
        "detection_type": detection_type,
        "dataset_ids": list(dataset_ids),
        "max_iterations": max_iter,
        "force_refresh": force_refresh,
    }
    if force_refresh and jailbreak_dataset_ids:
        config_data["jailbreak_dataset_ids"] = list(jailbreak_dataset_ids)
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
    user_id = ctx.obj.require_login()
    ds_list = asyncio.run(ctx.obj.scheduler.query_available_datasets(user_id=user_id))
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
        return
    groups = result.get("groups", [])
    if not groups:
        output.info("当前无活跃任务")
        return
    for g in groups:
        group_id_short = g.get("task_group_id", "")[:8]
        model_name = g.get("model_name", g.get("model_id", ""))
        status = g.get("status", "")
        prog = g.get("progress", {})
        total = prog.get("total", 0)
        completed = prog.get("completed", 0)
        failed = prog.get("failed", 0)
        running = prog.get("running", 0)
        pending = prog.get("pending", 0)
        click.echo(click.style(f"  任务组 {group_id_short}  模型: {model_name}  状态: {status}", fg="cyan"))
        click.echo(f"    进度: {completed}/{total} 完成, {running} 执行中, {pending} 等待, {failed} 失败")
        children = g.get("children", [])
        if children:
            child_rows = []
            for c in children:
                tid = c.get("task_id", "")[:8]
                cstatus = c.get("status", "")
                ds_name = c.get("dataset_name", c.get("dataset_id", ""))
                err = c.get("error_message", "")
                child_rows.append([tid, cstatus, ds_name, err[:40] if err else ""])
            output.table(["子任务ID", "状态", "数据集", "错误"], child_rows)
        click.echo("")


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


@detect_group.command("cancel")
@click.option("--task-id", default=None, help="取消单个任务")
@click.option("--group-id", default=None, help="取消整个任务组")
@click.pass_context
def cancel(ctx, task_id, group_id):
    """取消检测任务"""
    scheduler = ctx.obj.scheduler
    if group_id:
        result = asyncio.run(scheduler.cancel_task_group(group_id))
    elif task_id:
        result = asyncio.run(scheduler.cancel_task(task_id))
    else:
        output.error("必须提供 --task-id 或 --group-id")
        return
    if result.get("success"):
        output.success("已取消")
    else:
        output.error(result.get("error", "取消失败"))


@detect_group.command("dataset-detail")
@click.argument("dataset_id", type=int)
@click.pass_context
def dataset_detail(ctx, dataset_id):
    """查看数据集详情"""
    user_id = ctx.obj.require_login()
    dataset = asyncio.run(ctx.obj.scheduler.query_dataset_detail(dataset_id, user_id=user_id))
    if not dataset:
        output.info("数据集不存在")
        return
    output.kv(dataset)


@detect_group.command("dataset-export")
@click.argument("dataset_id", type=int)
@click.option("--output", "output_path", default=None, help="输出文件路径")
@click.pass_context
def dataset_export(ctx, dataset_id, output_path):
    """导出数据集文件"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.export_dataset_file(dataset_id, user_id=user_id))
    if not result:
        output.error("数据集不存在")
        return
    if "error" in result and "content" not in result:
        output.error(result["error"])
        return
    content = result["content"]
    if isinstance(content, str):
        content = content.encode("utf-8")
    filename = output_path or result.get("filename", f"dataset_{dataset_id}")
    pathlib.Path(filename).write_bytes(content)
    output.success(f"已导出至 {filename}")


@detect_group.command("dataset-delete")
@click.argument("dataset_id", type=int)
@click.confirmation_option(prompt="确认删除该数据集?")
@click.pass_context
def dataset_delete(ctx, dataset_id):
    """删除用户数据集"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.delete_user_dataset(dataset_id, user_id))
    if result.get("success"):
        output.success("删除成功")
    else:
        output.error(result.get("error", "删除失败"))


@detect_group.command("dataset-import")
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def dataset_import(ctx, file_path):
    """导入数据集文件"""
    user_id = ctx.obj.require_login()
    p = pathlib.Path(file_path)
    content = p.read_bytes()
    result = asyncio.run(ctx.obj.scheduler.import_dataset_file(
        user_id=user_id, filename=p.name, content=content
    ))
    if result.get("success"):
        output.success(f"导入成功, 数据集ID: {result.get('dataset_id')}")
    else:
        output.error(result.get("error", "导入失败"))


@detect_group.command("trace")
@click.option("--show-full", is_flag=True, default=False, help="显示完整内容（默认截断长文本）")
@click.pass_context
def trace(ctx, show_full):
    """实时追踪检测过程中的 LLM 请求与响应"""
    scheduler = ctx.obj.scheduler
    stop_event = threading.Event()

    def _on_llm_call(request_info: dict, response_info: dict) -> None:
        model_id = request_info.get("model_id", "?")
        user_msg = request_info.get("user_message", "")
        system_msg = request_info.get("system_prompt", "")

        if not show_full:
            if len(user_msg) > 120:
                user_msg = user_msg[:120] + "..."
            if len(system_msg) > 80:
                system_msg = system_msg[:80] + "..."

        click.echo(click.style(f"\n── REQUEST → {model_id} ──", fg="yellow"))
        if system_msg:
            click.echo(click.style("  [system] ", fg="cyan") + system_msg)
        click.echo(click.style("  [user]   ", fg="cyan") + user_msg)

        if "error" in response_info:
            click.echo(click.style("── RESPONSE ✗ ──", fg="red"))
            click.echo(click.style(f"  错误: {response_info['error']}", fg="red"))
        else:
            content = response_info.get("content", "")
            if not show_full and len(content) > 200:
                content = content[:200] + "..."
            usage = response_info.get("usage", {})
            usage_str = ""
            if usage:
                parts = []
                if "prompt_tokens" in usage:
                    parts.append(f"in={usage['prompt_tokens']}")
                if "completion_tokens" in usage:
                    parts.append(f"out={usage['completion_tokens']}")
                if "total_tokens" in usage:
                    parts.append(f"total={usage['total_tokens']}")
                usage_str = f" ({', '.join(parts)})" if parts else ""
            click.echo(click.style("── RESPONSE ✓ ──", fg="green") + usage_str)
            click.echo(f"  {content}")

    scheduler.subscribe_llm_calls(_on_llm_call)
    click.echo(click.style("正在监听 LLM 调用... (Ctrl+C 退出)", fg="bright_white"))
    try:
        while not stop_event.is_set():
            stop_event.wait(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.unsubscribe_llm_calls(_on_llm_call)
        click.echo(click.style("\n已停止监听", fg="bright_white"))
