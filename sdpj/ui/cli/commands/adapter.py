"""私有资源交互命令 (职责 14-15)"""
import asyncio
import click

from sdpj.ui.cli.utils import output


@click.group("config")
def config_group():
    """私有检测配置与资源管理"""
    pass


# ── 私有检测配置 (职责 14) ──

@config_group.command("create")
@click.argument("config_file", type=click.Path(exists=True))
@click.pass_context
def create_config(ctx, config_file):
    """创建私有检测配置"""
    import json
    user_id = ctx.obj.require_login()
    with open(config_file, "r", encoding="utf-8") as f:
        content = json.load(f)
    result = asyncio.run(ctx.obj.scheduler.schedule_config_operation(
        "create", {"user_id": user_id, "config_content": content}
    ))
    if result["success"]:
        output.success(f"配置已创建, ID: {result.get('config_id')}")
    else:
        output.error(result.get("error", "创建失败"))


@config_group.command("list")
@click.pass_context
def list_configs(ctx):
    """列出私有检测配置清单"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.schedule_config_operation(
        "list", {"user_id": user_id}
    ))
    configs = result.get("configs", [])
    if not configs:
        output.info("暂无配置")
        return
    rows = [[str(c.get("id", "")), c.get("name", ""), c.get("model_id", "")] for c in configs]
    output.table(["ID", "名称", "模型"], rows)


@config_group.command("view")
@click.argument("config_id", type=int)
@click.pass_context
def view_config(ctx, config_id):
    """读取私有检测配置"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.schedule_config_operation(
        "read", {"user_id": user_id, "config_id": config_id}
    ))
    if result["success"] and result.get("config"):
        output.kv(result["config"])
    else:
        output.error(result.get("error", "读取失败"))


@config_group.command("delete")
@click.argument("config_id", type=int)
@click.pass_context
def delete_config(ctx, config_id):
    """删除私有检测配置"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.schedule_config_operation(
        "delete", {"user_id": user_id, "config_id": config_id}
    ))
    if result["success"]:
        output.success("配置已删除")
    else:
        output.error(result.get("error", "删除失败"))


@config_group.command("export")
@click.argument("config_id", type=int)
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "yaml"]))
@click.option("--output", "output_path", default=None, help="输出文件路径")
@click.pass_context
def export_config(ctx, config_id, fmt, output_path):
    """导出私有检测配置"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.schedule_config_operation(
        "export", {"user_id": user_id, "config_id": config_id, "format": fmt}
    ))
    if not result["success"]:
        output.error(result.get("error", "导出失败"))
        return
    content = result.get("content", "")
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        output.success(f"已导出至 {output_path}")
    else:
        click.echo(content)


@config_group.command("update")
@click.argument("config_id", type=int)
@click.argument("config_file", type=click.Path(exists=True))
@click.pass_context
def update_config(ctx, config_id, config_file):
    """更新私有检测配置"""
    import json
    user_id = ctx.obj.require_login()
    with open(config_file, "r", encoding="utf-8") as f:
        content = json.load(f)
    result = asyncio.run(ctx.obj.scheduler.schedule_config_operation(
        "update", {"user_id": user_id, "config_id": config_id, "config_content": content}
    ))
    if result["success"]:
        output.success("配置已更新")
    else:
        output.error(result.get("error", result.get("message", "更新失败")))


@config_group.command("import")
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def import_config(ctx, file_path):
    """导入私有检测配置"""
    user_id = ctx.obj.require_login()
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    result = asyncio.run(ctx.obj.scheduler.schedule_config_operation(
        "import", {"user_id": user_id, "file_content": content}
    ))
    if result["success"]:
        output.success(f"配置已导入, ID: {result.get('config_id')}")
    else:
        output.error(result.get("error", "导入失败"))


# ── 私有大模型适配器与数据集 (职责 15) ──

@config_group.command("upload-adapter")
@click.argument("adapter_file", type=click.Path(exists=True))
@click.option("--model-id", required=True, help="目标大模型标识")
@click.pass_context
def upload_adapter(ctx, adapter_file, model_id):
    """上传私有大模型适配器"""
    user_id = ctx.obj.require_login()
    with open(adapter_file, "r", encoding="utf-8") as f:
        content = f.read()
    result = asyncio.run(ctx.obj.scheduler.schedule_private_resource_operation(
        "upload_adapter", {"user_id": user_id, "adapter_content": content, "model_id": model_id}
    ))
    if result["success"]:
        output.success(f"适配器已上传, 资源ID: {result.get('resource_id')}")
    else:
        output.error(result.get("message", "上传失败"))


@config_group.command("remove-adapter")
@click.option("--model-id", required=True, help="大模型标识")
@click.option("--resource-id", required=True, type=int, help="资源ID")
@click.pass_context
def remove_adapter(ctx, model_id, resource_id):
    """移除私有大模型适配器"""
    user_id = ctx.obj.require_login()
    params = {"user_id": user_id, "model_id": model_id, "resource_id": resource_id}
    result = asyncio.run(ctx.obj.scheduler.schedule_private_resource_operation(
        "remove_adapter", params
    ))
    if result["success"]:
        output.success("适配器已移除")
    else:
        output.error(result.get("message", "移除失败"))


@config_group.command("upload-dataset")
@click.argument("dataset_file", type=click.Path(exists=True))
@click.option("--name", required=True, help="数据集名称")
@click.option("--risk-type", required=True, help="风险类型")
@click.pass_context
def upload_dataset(ctx, dataset_file, name, risk_type):
    """上传私有数据集"""
    import json
    user_id = ctx.obj.require_login()
    with open(dataset_file, "r", encoding="utf-8") as f:
        samples = json.load(f)
    result = asyncio.run(ctx.obj.scheduler.schedule_private_resource_operation(
        "upload_dataset", {
            "user_id": user_id, "name": name,
            "risk_type": risk_type, "samples": samples,
        }
    ))
    if result["success"]:
        output.success("数据集已上传")
        output.kv(result.get("info", {}))
    else:
        output.error("上传失败")


@config_group.command("remove-dataset")
@click.argument("dataset_id", type=int)
@click.option("--resource-id", type=int, default=None, help="资源ID")
@click.pass_context
def remove_dataset(ctx, dataset_id, resource_id):
    """移除私有数据集"""
    user_id = ctx.obj.require_login()
    params = {"user_id": user_id, "dataset_id": dataset_id}
    if resource_id is not None:
        params["resource_id"] = resource_id
    result = asyncio.run(ctx.obj.scheduler.schedule_private_resource_operation(
        "remove_dataset", params
    ))
    if result["success"]:
        output.success("数据集已移除")
    else:
        output.error(result.get("error", "移除失败"))
