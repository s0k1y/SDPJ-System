"""基于令牌桶的异步请求速率控制器"""
import asyncio
import time


class RateLimiter:
    """令牌桶速率限制器

    控制每秒最大请求数（max_rps），确保请求速率不超过 API 限制。
    用法：在每次 API 调用前 await limiter.acquire()

    与互斥锁实现的关键区别：
    - 令牌桶允许并发 acquire()，只要桶中有令牌即可立即通过
    - 锁仅保护令牌计数的读写（微秒级），不保护 sleep
    - sleep 在锁外执行，不阻塞其他协程
    """

    def __init__(self, max_rps: float = 0.5):
        self._rate = max_rps
        self._tokens = max_rps
        self._max_tokens = max_rps
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(self._max_tokens, self._tokens + elapsed * self._rate)
            self._last_refill = now

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = (1.0 - self._tokens) / self._rate
            await asyncio.sleep(wait)
