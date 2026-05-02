"""CLI 命令行界面"""
import asyncio
import click
from sdpj.control.state_scheduler import StateScheduler


@click.group()
def cli():
    """SDPJ-System 命令行工具"""
    pass


@cli.command()
@click.option('--username', prompt='用户名', help='用户名')
@click.option('--password', prompt='密码', hide_input=True, help='密码')
def register(username, password):
    """注册新用户"""
    async def _register():
        scheduler = StateScheduler()
        await scheduler.init()
        result = await scheduler.register_user(username, password)
        if result["success"]:
            click.echo(f"✓ {result['message']}")
        else:
            click.echo(f"✗ {result['message']}", err=True)
    
    asyncio.run(_register())


@cli.command()
@click.option('--username', prompt='用户名', help='用户名')
@click.option('--password', prompt='密码', hide_input=True, help='密码')
def login(username, password):
    """用户登录"""
    async def _login():
        scheduler = StateScheduler()
        await scheduler.init()
        result = await scheduler.login_user(username, password)
        if result["success"]:
            click.echo(f"✓ 登录成功，会话ID: {result['session_id']}")
        else:
            click.echo("✗ 登录失败", err=True)
    
    asyncio.run(_login())


@cli.command()
@click.option('--model-id', required=True, help='模型ID')
@click.option('--dataset-id', required=True, type=int, help='数据集ID')
@click.option('--algorithm', default='static', help='检测算法类型')
def detect(model_id, dataset_id, algorithm):
    """启动检测任务"""
    async def _detect():
        scheduler = StateScheduler()
        await scheduler.init()
        
        config_data = {
            "model_id": model_id,
            "dataset_id": dataset_id,
            "algorithm_type": algorithm
        }
        
        result = await scheduler.start_detection(user_id=1, config_data=config_data)
        if result["success"]:
            click.echo(f"✓ 检测任务已启动，任务ID: {result['task_id']}")
        else:
            click.echo(f"✗ 启动失败: {result['error']}", err=True)
    
    asyncio.run(_detect())


@cli.command()
def status():
    """查询系统状态"""
    scheduler = StateScheduler()
    state = scheduler.get_system_state()
    click.echo(f"系统状态: {state}")


if __name__ == '__main__':
    cli()
