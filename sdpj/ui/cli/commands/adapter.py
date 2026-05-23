"""私有资源交互命令 (职责 14-15)"""

import asyncio
import pathlib

import click

from sdpj.ui.cli import OrderedGroup
from sdpj.ui.cli.utils import output
from sdpj.ui.cli.utils.result import unwrap


@click.group("Config", cls=OrderedGroup, no_args_is_help=True)
def config_group():
    """私有检测配置与资源管理"""


# ── 检测配置 CRUD (职责 14) ──


@config_group.command("create")
@click.option("--model", required=True, help="模型标识(如 deepseek-v4-pro)")
@click.option("--request-format", required=True, help="请求格式(openai/anthropic/custom)")
@click.option("--api-key", required=True, help="API 密钥")
@click.option("--base-url", required=True, help="API 地址(如 https://api.deepseek.com)")
@click.option("--timeout", required=True, type=int, help="请求超时秒数")
@click.option("--max-rps", required=True, type=float, help="每秒最大请求数")
@click.option("--max-concurrency", required=True, type=int, help="最大并发数")
@click.pass_context
def create_config(ctx, model, request_format, api_key, base_url, timeout, max_rps, max_concurrency):
    """创建私有检测配置并自动注册适配器"""
    content = {
        "model": model,
        "model_id": model,
        "request_format": request_format,
        "api_key": api_key,
        "base_url": base_url,
        "timeout": timeout,
        "max_rps": max_rps,
        "max_concurrency": max_concurrency,
    }
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_config_operation("create", {"user_id": user_id, "config_content": content})
    )
    data = unwrap(result)
    output.success(f"配置已创建, ID: {data.get('config_id')}")
    if data.get("message"):
        output.info(data["message"])


@config_group.command("list")
@click.pass_context
def list_configs(ctx):
    """列出私有检测配置清单"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.schedule_config_operation("list", {"user_id": user_id}))
    configs = result.get("configs", [])
    if not configs:
        output.info("暂无配置")
        return
    rows = [[str(c.get("config_id", "")), c.get("content", {}).get("model_id") or c.get("content", {}).get("model", ""), c.get("content", {}).get("request_format", "")] for c in configs]
    output.table(["ID", "模型", "请求格式"], rows)


@config_group.command("view")
@click.option("--config-id", required=True, type=int, help="配置ID")
@click.pass_context
def view_config(ctx, config_id):
    """读取私有检测配置"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_config_operation("read", {"user_id": user_id, "config_id": config_id})
    )
    data = unwrap(result, required="config")
    output.kv(data["config"])


@config_group.command("update")
@click.option("--config-id", required=True, type=int, help="配置ID")
@click.option("--model", required=True, help="模型标识(如 deepseek-v4-pro)")
@click.option("--request-format", required=True, help="请求格式(openai/anthropic/custom)")
@click.option("--api-key", required=True, help="API 密钥")
@click.option("--base-url", required=True, help="API 地址(如 https://api.deepseek.com)")
@click.option("--timeout", required=True, type=int, help="请求超时秒数")
@click.option("--max-rps", required=True, type=float, help="每秒最大请求数")
@click.option("--max-concurrency", required=True, type=int, help="最大并发数")
@click.pass_context
def update_config(ctx, config_id, model, request_format, api_key, base_url, timeout, max_rps, max_concurrency):
    """更新私有检测配置"""
    content = {
        "model": model,
        "model_id": model,
        "request_format": request_format,
        "api_key": api_key,
        "base_url": base_url,
        "timeout": timeout,
        "max_rps": max_rps,
        "max_concurrency": max_concurrency,
    }
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_config_operation(
            "update", {"user_id": user_id, "config_id": config_id, "config_content": content}
        )
    )
    unwrap(result)
    output.success("配置已更新")


@config_group.command("delete")
@click.option("--config-id", required=True, type=int, help="配置ID")
@click.confirmation_option(prompt="确认删除该配置?")
@click.pass_context
def delete_config(ctx, config_id):
    """删除私有检测配置"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_config_operation("delete", {"user_id": user_id, "config_id": config_id})
    )
    unwrap(result)
    output.success("配置已删除")


# ── 配置导入导出 ──


@config_group.command("import")
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def import_config(ctx, file_path):
    """导入私有检测配置并自动注册适配器"""
    import os

    user_id = ctx.obj.require_login()
    abs_path = os.path.abspath(file_path)
    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_config_operation("import", {"user_id": user_id, "file_content": content})
    )
    data = unwrap(result)
    output.success(f"配置已导入, ID: {data.get('config_id')}")
    if data.get("message"):
        output.info(data["message"])


@config_group.command("export")
@click.option("--config-id", required=True, type=int, help="配置ID")
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "yaml"]))
@click.option("--output", "output_path", default=None, help="输出文件路径")
@click.pass_context
def export_config(ctx, config_id, fmt, output_path):
    """导出私有检测配置"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_config_operation(
            "export", {"user_id": user_id, "config_id": config_id, "format": fmt}
        )
    )
    data = unwrap(result)
    content = data.get("content", "")
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        output.success(f"已导出至 {output_path}")
    else:
        click.echo(content)


# ── 配置可用性验证 ──


@config_group.command("verify")
@click.option("--config-id", required=True, type=int, help="配置ID")
@click.pass_context
def verify_config(ctx, config_id):
    """测试私有检测配置的可用性"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_config_operation("verify", {"user_id": user_id, "config_id": config_id})
    )
    data = unwrap(result)
    status_info = data.get("result", {})
    status = status_info.get("status", "unknown")

    status_labels = {
        "ok": "连接正常",
        "auth_failed": "认证失败",
        "unreachable": "无法连接",
        "timeout": "连接超时",
        "format_mismatch": "响应格式不匹配",
        "config_error": "配置错误",
    }
    label = status_labels.get(status, f"未知状态 ({status})")

    if status == "ok":
        output.success(f"{label}  |  模型: {status_info.get('model', '-')}  |  延迟: {status_info.get('latency_ms', '-')}ms")
        preview = status_info.get("response_preview", "")
        if preview:
            output.info(f"响应预览: {preview}")
    else:
        output.error(f"{label}  |  {status_info.get('error', '')}")


# ── 私有数据集 ──


@config_group.command("upload-dataset")
@click.argument("dataset_file", type=click.Path(exists=True))
@click.pass_context
def upload_dataset(ctx, dataset_file):
    """上传私有数据集"""
    import json
    import os

    user_id = ctx.obj.require_login()
    abs_path = os.path.abspath(dataset_file)
    name = os.path.splitext(os.path.basename(abs_path))[0]
    with open(abs_path, "r", encoding="utf-8") as f:
        raw = f.read()
    if abs_path.endswith(".jsonl"):
        samples = [json.loads(line) for line in raw.strip().splitlines() if line.strip()]
    else:
        loaded = json.loads(raw)
        samples = loaded if isinstance(loaded, list) else loaded.get("samples", [loaded])
    risk_type = samples[0].get("subtype", "custom") if samples else "custom"
    result = asyncio.run(
        ctx.obj.scheduler.schedule_private_resource_operation(
            "upload_dataset",
            {
                "user_id": user_id,
                "name": name,
                "risk_type": risk_type,
                "samples": samples,
            },
        )
    )
    data = unwrap(result)
    output.success("数据集已上传")
    output.kv(data.get("info", {}))


@config_group.command("remove-dataset")
@click.option("--dataset-id", required=True, type=int, help="数据集ID")
@click.option("--resource-id", type=int, default=None, help="资源ID")
@click.confirmation_option(prompt="确认移除该数据集?")
@click.pass_context
def remove_dataset(ctx, dataset_id, resource_id):
    """移除私有数据集"""
    user_id = ctx.obj.require_login()
    params = {"user_id": user_id, "dataset_id": dataset_id}
    if resource_id is not None:
        params["resource_id"] = resource_id
    result = asyncio.run(ctx.obj.scheduler.schedule_private_resource_operation("remove_dataset", params))
    unwrap(result)
    output.success("数据集已移除")


# ── 数据集导出 ──


@config_group.command("export-dataset")
@click.option("--id", "dataset_id", required=True, type=int, help="数据集ID")
@click.option("--output", "output_path", default=None, help="输出文件路径")
@click.pass_context
def export_dataset(ctx, dataset_id, output_path):
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
    dest = pathlib.Path(filename)
    if dest.is_dir():
        dest = dest / result.get("filename", f"dataset_{dataset_id}")
    dest.write_bytes(content)
    output.success(f"已导出至 {dest}")


# ── 数据集管理子命令组 ──


@config_group.group("dataset", cls=OrderedGroup, no_args_is_help=True)
def dataset_group():
    """数据集管理"""


@dataset_group.command("list")
@click.pass_context
def dataset_list(ctx):
    """列出可用数据集"""
    user_id = ctx.obj.require_login()
    ds_list = asyncio.run(ctx.obj.scheduler.query_available_datasets(user_id=user_id))
    if not ds_list:
        output.info("暂无可用数据集")
        return
    rows = [[str(d.get("dataset_id", "")), d.get("name", ""), str(d.get("sample_count", 0))] for d in ds_list]
    output.table(["ID", "名称", "样本数"], rows)


@dataset_group.command("detail")
@click.option("--id", required=True, type=int, help="数据集ID")
@click.pass_context
def dataset_detail(ctx, id):
    """查看数据集详情"""
    user_id = ctx.obj.require_login()
    dataset = asyncio.run(ctx.obj.scheduler.query_dataset_detail(id, user_id=user_id))
    if not dataset:
        output.info("数据集不存在")
        return
    output.kv(dataset)
