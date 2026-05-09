"""用户账号与权限交互命令 (职责 11-13)"""

import asyncio

import click

from sdpj.ui.cli.utils import output


@click.group("user")
def user_group():
    """用户账号与权限管理"""


@user_group.command("register")
@click.option("--username", prompt="用户名", help="用户名")
@click.option("--password", prompt="密码", hide_input=True, help="密码")
@click.pass_context
def register(ctx, username, password):
    """注册新用户"""
    result = asyncio.run(ctx.obj.scheduler.schedule_user_auth(username, password, "register"))
    if result["success"]:
        output.success(result.get("message", "注册成功"))
    else:
        output.error(result.get("message", "注册失败"))


@user_group.command("login")
@click.option("--username", prompt="用户名", help="用户名")
@click.option("--password", prompt="密码", hide_input=True, help="密码")
@click.pass_context
def login(ctx, username, password):
    """用户登录"""
    result = asyncio.run(ctx.obj.scheduler.schedule_user_auth(username, password, "login"))
    if result["success"]:
        ctx.obj.current_user_id = result.get("user_id")
        output.success(f"登录成功, 用户ID: {result.get('user_id')}")
    else:
        output.error("登录失败")


@user_group.command("logout")
@click.pass_context
def logout(ctx):
    """用户登出"""
    user_id = ctx.obj.current_user_id
    params = {"user_id": user_id} if user_id else {}
    asyncio.run(ctx.obj.scheduler.schedule_account_operation("logout", params))
    ctx.obj.current_user_id = None
    output.success("已登出")


@user_group.command("profile")
@click.pass_context
def profile(ctx):
    """查询当前用户资料"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.schedule_account_operation("get_profile", {"user_id": user_id}))
    if result["success"] and result.get("profile"):
        output.kv(result["profile"])
    else:
        output.info("未登录或无资料")


@user_group.command("password")
@click.option("--old", "old_password", prompt="旧密码", hide_input=True)
@click.option("--new", "new_password", prompt="新密码", hide_input=True)
@click.pass_context
def change_password(ctx, old_password, new_password):
    """修改当前用户密码"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_account_operation(
            "change_password", {"user_id": user_id, "old_password": old_password, "new_password": new_password}
        )
    )
    if result["success"]:
        output.success("密码已修改")
    else:
        output.error(result.get("message", "修改失败"))


@user_group.command("switch")
@click.option("--username", prompt="用户名", help="目标用户名")
@click.option("--password", prompt="密码", hide_input=True, help="密码")
@click.pass_context
def switch(ctx, username, password):
    """切换账号"""
    result = asyncio.run(
        ctx.obj.scheduler.schedule_account_operation("switch_account", {"username": username, "password": password})
    )
    if result["success"]:
        ctx.obj.current_user_id = result.get("user_id")
        output.success(f"已切换至用户 {result.get('user_id')}")
    else:
        output.error("切换失败")


@user_group.command("unregister")
@click.confirmation_option(prompt="确认注销当前账号?")
@click.pass_context
def unregister(ctx):
    """注销当前账号"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.schedule_account_operation("unregister", {"user_id": user_id}))
    if result["success"]:
        ctx.obj.current_user_id = None
        output.success("账号已注销")
    else:
        output.error(result.get("message", "注销失败"))


@user_group.command("resources")
@click.pass_context
def resources(ctx):
    """列出当前用户拥有的受控资源"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(ctx.obj.scheduler.schedule_account_operation("list_resources", {"user_id": user_id}))
    res_list = result.get("resources", [])
    shared_list = result.get("shared_resources", [])
    if not res_list and not shared_list:
        output.info("暂无受控资源")
        return
    if res_list:
        output.info("自有资源:")
        rows = [[str(r.get("id", "")), r.get("type", ""), r.get("name", "")] for r in res_list]
        output.table(["ID", "类型", "名称"], rows)
    if shared_list:
        output.info("共享资源:")
        rows = [[str(r.get("id", "")), r.get("type", ""), r.get("name", "")] for r in shared_list]
        output.table(["ID", "类型", "名称"], rows)


@user_group.command("list")
@click.pass_context
def list_users(ctx):
    """列出所有用户"""
    users = asyncio.run(ctx.obj.scheduler.list_all_users())
    if not users:
        output.info("暂无用户")
        return
    rows = [[str(u.get("user_id", "")), u.get("username", ""), u.get("created_at", "-")] for u in users]
    output.table(["用户ID", "用户名", "创建时间"], rows)


@user_group.command("delete-user")
@click.option("--user-id", required=True, type=int, help="目标用户ID")
@click.confirmation_option(prompt="确认删除该用户?")
@click.pass_context
def delete_user(ctx, user_id):
    """管理员删除用户"""
    result = asyncio.run(ctx.obj.scheduler.schedule_account_operation("admin_delete_user", {"user_id": user_id}))
    if result["success"]:
        output.success(result.get("message", "用户已删除"))
    else:
        output.error(result.get("message", "删除失败"))


@user_group.command("update-profile")
@click.option("--username", required=True, help="新用户名")
@click.pass_context
def update_profile(ctx, username):
    """更新当前用户资料"""
    user_id = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_account_operation("update_profile", {"user_id": user_id, "username": username})
    )
    if result["success"]:
        output.success("资料已更新")
    else:
        output.error(result.get("message", result.get("error", "更新失败")))


# ── 权限授权子命令 (职责 13) ──


@user_group.group("auth")
def auth_group():
    """访问授权管理"""


@auth_group.command("grant")
@click.option("--resource-id", required=True, type=int, help="资源ID")
@click.option("--target-username", required=True, help="被授权用户名")
@click.pass_context
def grant(ctx, resource_id, target_username):
    """授予其他用户对私有资源的读权限"""
    caller = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_dac_operation(
            "grant",
            {
                "resource_id": resource_id,
                "target_username": target_username,
                "caller_user_id": caller,
            },
        )
    )
    if result["success"]:
        output.success(result.get("message", "已授权"))
    else:
        output.error(result.get("message", "授权失败"))


@auth_group.command("revoke")
@click.option("--acl-id", required=True, type=int, help="访问控制项ID")
@click.pass_context
def revoke(ctx, acl_id):
    """移除已授予的读权限"""
    caller = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_dac_operation(
            "revoke",
            {
                "acl_id": acl_id,
                "caller_user_id": caller,
            },
        )
    )
    if result["success"]:
        output.success(result.get("message", "已移除"))
    else:
        output.error(result.get("message", "移除失败"))


@auth_group.command("list")
@click.option("--resource-id", required=True, type=int, help="资源ID")
@click.pass_context
def list_acl(ctx, resource_id):
    """查询某资源的授权清单"""
    caller = ctx.obj.require_login()
    result = asyncio.run(
        ctx.obj.scheduler.schedule_dac_operation(
            "list",
            {
                "resource_id": resource_id,
                "caller_user_id": caller,
            },
        )
    )
    if not result["success"]:
        output.error("查询失败")
        return
    acl_list = result.get("acl_list", [])
    if not acl_list:
        output.info("暂无授权记录")
        return
    rows = [[str(a.get("id", "")), str(a.get("user_id", "")), a.get("permission", "")] for a in acl_list]
    output.table(["ACL-ID", "用户ID", "权限"], rows)
