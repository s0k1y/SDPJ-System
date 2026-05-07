"""CPU 密集型操作异步卸载工具

将同步的 CPU 密集操作卸载到 ThreadPoolExecutor 中执行，
避免阻塞 asyncio 事件循环。
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Callable, TypeVar

T = TypeVar("T")

_cpu_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="sdpj-cpu")


async def run_cpu(func: Callable[..., T], *args, **kwargs) -> T:
    """将同步 CPU 密集操作卸载到线程池执行

    Args:
        func: 同步函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        函数执行结果
    """
    loop = asyncio.get_running_loop()
    if kwargs:
        return await loop.run_in_executor(_cpu_executor, partial(func, *args, **kwargs))
    return await loop.run_in_executor(_cpu_executor, func, *args)
