"""用户账号与权限交互命令 (职责 11-13)."""

import asyncio

import click

from sdpj.ui.cli import OrderedGroup, require_scheduler
from sdpj.ui.cli.schemas.user import AuthParams
from sdpj.ui.cli.session import clear_session, save_session
from sdpj.ui.cli.utils import output
from sdpj.ui.cli.utils.result import unwrap


@click.group("User", cls=OrderedGroup, no_args_is_help=True)
def user_group() -> None:
    """用户账号与权限管理."""


# ── 账号生命周期 (注册→登录→登出→切换) ──


@user_group.command("register")
@click.option("--username", prompt="用户名", help="用户名")
@click.option("--password", prompt="密码", hide_input=True, help="密码")
@click.pass_context
@require_scheduler
def register(ctx, username, password) -> None:  # noqa: ANN001
    """注册新用户."""
    params = AuthParams(username=username, password=password)
    result = asyncio.run(
        ctx.obj.scheduler.schedule_user_auth(params.username, params.password, "register"),
    )
    data = unwrap(result)
    output.success(data.get("message", "注册成功"))


@user_group.command("login")
@click.option("--username", prompt="用户名", help="用户名")
@click.option("--password", prompt="密码", hide_input=True, help="密码")
@click.pass_context
@require_scheduler
def login(ctx, username, password) -> None:  # noqa: ANN001
    """用户登录."""
    params = AuthParams(username=username, password=password)
    result = asyncio.run(
        ctx.obj.scheduler.schedule_user_auth(params.username, params.password, "login"),
    )
    data = unwrap(result, required="user_id")
    ctx.obj.current_user_id = data["user_id"]
    save_session(data["user_id"])
    output.success(f"登录成功, 用户ID: {data['user_id']}")


@user_group.command("logout")
@click.pass_context
@require_scheduler
def logout(ctx) -> None:  # noqa: ANN001
    """用户登出."""
    user_id = ctx.obj.current_user_id
    params = {"user_id": user_id} if user_id else {}
    asyncio.run(ctx.obj.scheduler.schedule_account_operation("logout", params))
    ctx.obj.current_user_id = None
    clear_session()
    output.success("已登出")


@user_group.command("switch")
@click.option("--username", prompt="用户名", help="目标用户名")
@click.option("--password", prompt="密码", hide_input=True, help="密码")
@click.pass_context
@require_scheduler
def switch(ctx, username, password) -> None:  # noqa: ANN001
    """切换账号."""
    result = asyncio.run(
        ctx.obj.scheduler.schedule_account_operation(
            "switch_account", {"username": username, "password": password},
        ),
    )
    data = unwrap(result, required="user_id")
    ctx.obj.current_user_id = data["user_id"]
    save_session(data["user_id"])
    output.success(f"已切换至用户 {data['user_id']}")


# ── 资料与安全 ──


@user_group.command("profile")
@click.pass_context
@require_scheduler
def profile(ctx) -> None:  # noqa: ANN001
    """查询当前用户资料."""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_account_operation("get_profile", {"user_id": user_id}),
    )
    data = unwrap(result, required="profile")
    output.kv(data["profile"])


@user_group.command("password")
@click.option("--old", "old_password", prompt="旧密码", hide_input=True)
@click.option("--new", "new_password", prompt="新密码", hide_input=True)
@click.pass_context
@require_scheduler
def change_password(ctx, old_password, new_password) -> None:  # noqa: ANN001
    """修改当前用户密码."""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_account_operation(
            "change_password",
            {"user_id": user_id, "old_password": old_password, "new_password": new_password},
        ),
    )
    unwrap(result)
    output.success("密码已修改")


# ── 注销与资源 ──


@user_group.command("unregister")
@click.confirmation_option(prompt="确认注销当前账号?")
@click.pass_context
@require_scheduler
def unregister(ctx) -> None:  # noqa: ANN001
    """注销当前账号."""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_account_operation("unregister", {"user_id": user_id}),
    )
    unwrap(result)
    ctx.obj.current_user_id = None
    clear_session()
    output.success("账号已注销")


@user_group.command("resources")
@click.pass_context
@require_scheduler
def resources(ctx) -> None:  # noqa: ANN001
    """列出当前用户拥有的受控资源."""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_account_operation("list_resources", {"user_id": user_id}),
    )
    res_list = result.get("resources", [])
    shared_list = result.get("shared_resources", [])
    if not res_list and not shared_list:
        output.info("暂无受控资源")
        return
    if res_list:
        output.info("自有资源:")
        rows = [
            [
                str(r.get("resource_id", "")),
                r.get("resource_type", ""),
                (r.get("dataset_name") or r.get("model_id") or ""),
            ]
            for r in res_list
        ]
        output.table(["ID", "类型", "名称"], rows)
    if shared_list:
        output.info("共享资源:")
        rows = [
            [
                str(r.get("resource_id", "")),
                r.get("resource_type", ""),
                (r.get("dataset_name") or r.get("model_id") or ""),
            ]
            for r in shared_list
        ]
        output.table(["ID", "类型", "名称"], rows)


# ── 权限授权子命令 (职责 13) ──


@user_group.group("auth", cls=OrderedGroup, no_args_is_help=True)
def auth_group() -> None:
    """访问授权管理."""


@auth_group.command("grant")
@click.option("--resource-id", required=True, type=int, help="资源ID")
@click.option("--target-username", required=True, help="被授权用户名")
@click.pass_context
@require_scheduler
def grant(ctx, resource_id, target_username) -> None:  # noqa: ANN001
    """授予其他用户对私有资源的读权限."""
    caller = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_dac_operation(
            "grant",
            {
                "resource_id": resource_id,
                "target_username": target_username,
                "caller_user_id": caller,
            },
        ),
    )
    data = unwrap(result)
    output.success(data.get("message", "已授权"))


@auth_group.command("revoke")
@click.option("--acl-id", required=True, type=int, help="访问控制项ID")
@click.pass_context
@require_scheduler
def revoke(ctx, acl_id) -> None:  # noqa: ANN001
    """移除已授予的读权限."""
    caller = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_dac_operation(
            "revoke",
            {
                "acl_id": acl_id,
                "caller_user_id": caller,
            },
        ),
    )
    data = unwrap(result)
    output.success(data.get("message", "已移除"))


@auth_group.command("show")
@click.option("--resource-id", required=True, type=int, help="资源ID")
@click.pass_context
@require_scheduler
def show_acl(ctx, resource_id) -> None:  # noqa: ANN001
    """查询指定资源的授权清单."""
    caller = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_dac_operation(
            "list",
            {
                "resource_id": resource_id,
                "caller_user_id": caller,
            },
        ),
    )
    data = unwrap(result)
    acl_list = data.get("acl_list", [])
    if not acl_list:
        output.info("暂无授权记录")
        return
    rows = [
        [str(a.get("acl_id", "")), str(a.get("grantee_user_id", "")), a.get("grantee_username", "")]
        for a in acl_list
    ]
    output.table(["ACL-ID", "用户ID", "用户名"], rows)


@auth_group.command("check")
@click.option("--resource-id", required=True, type=int, help="资源ID")
@click.pass_context
@require_scheduler
def check_access(ctx, resource_id) -> None:  # noqa: ANN001
    """检查当前用户对指定资源的访问权限."""
    user_id = ctx.obj.require_login()
    has_access = asyncio.run(ctx.obj.scheduler.check_resource_access(resource_id, user_id))
    if has_access:
        output.success(f"有访问权限 (resource_id={resource_id})")
    else:
        output.info(f"无访问权限 (resource_id={resource_id})")


# ── 管理员命令 ──


@user_group.command("list")
@click.pass_context
@require_scheduler
def list_users(ctx) -> None:  # noqa: ANN001
    """列出所有用户."""
    users = asyncio.run(ctx.obj.scheduler.list_all_users())
    if not users:
        output.info("暂无用户")
        return
    rows = [
        [str(u.get("user_id", "")), u.get("username", ""), u.get("created_at", "-")] for u in users
    ]
    output.table(["用户ID", "用户名", "创建时间"], rows)


@user_group.command("delete-user")
@click.option("--user-id", required=True, type=int, help="目标用户ID")
@click.confirmation_option(prompt="确认删除该用户?")
@click.pass_context
@require_scheduler
def delete_user(ctx, user_id) -> None:  # noqa: ANN001
    """管理员删除用户."""
    result = asyncio.run(
        ctx.obj.scheduler.schedule_account_operation("admin_delete_user", {"user_id": user_id}),
    )
    data = unwrap(result)
    output.success(data.get("message", "用户已删除"))
