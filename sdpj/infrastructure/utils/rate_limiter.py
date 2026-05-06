"""基于时间窗口的异步请求速率控制器"""
import asyncio
import time


class RateLimiter:
    """滑动窗口速率限制器

    控制每秒最大请求数（max_rps），确保请求速率不超过 API 限制。
    用法：在每次 API 调用前 await limiter.acquire()
    """

    def __init__(self, max_rps: float = 0.5):
        self._min_interval = 1.0 / max_rps
        self._last_time: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_time
            wait = self._min_interval - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_time = time.monotonic()
