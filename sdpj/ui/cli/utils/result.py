"""统一结果处理 — 对齐 WebUI response.py."""

import click


def unwrap(result: dict, *, required: str | None = None) -> dict:
    """从 scheduler 返回的 {success, ...} 字典中提取数据..

    失败时抛出 ClickException(Click 框架统一捕获并输出错误).
    required 指定必须存在的字段名,缺失时抛出异常.

    返回去除 success/error/message 包装后的纯数据字典.
    """
    if not isinstance(result, dict):
        return {"data": result}

    if result.get("success") is False:
        msg = result.get("error") or result.get("message") or "操作失败"
        raise click.ClickException(msg)

    if required is not None and required not in result:
        msg_0 = f"返回数据缺少必要字段: {required}"
        raise click.ClickException(msg_0)

    return {k: v for k, v in result.items() if k not in ("success", "error", "message")}
