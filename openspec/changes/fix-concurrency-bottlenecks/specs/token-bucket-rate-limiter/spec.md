# Token Bucket Rate Limiter 规格

## 概述
令牌桶速率控制器，替代当前互斥锁实现的 RateLimiter，支持真正的并发限速。

## 需求

### REQ-1：令牌桶算法
- RateLimiter 内部使用令牌桶算法替代互斥锁 + sleep 方案
- 令牌以 `max_rps` 速率持续添加到桶中
- 桶容量（`_max_tokens`）等于 `max_rps`，允许短时突发
- `acquire()` 从桶中取一个令牌，有令牌时立即返回（无锁等待）
- 桶空时计算等待时间，在锁外 sleep 后重试

### REQ-2：接口兼容性
- `acquire()` 方法签名不变：`async def acquire(self) -> None`
- `__init__` 参数不变：`max_rps: float = 0.5`
- 所有现有调用方无需修改

### REQ-3：并发安全
- 令牌计数的读写使用 `asyncio.Lock` 保护，但锁仅保护微秒级的计数操作
- sleep 操作在锁外执行，不阻塞其他协程
- 多个协程可以同时通过 acquire()，只要桶中有足够令牌

### REQ-4：限速语义
- 长期平均速率不超过 `max_rps`
- 短时允许突发（桶中有累积令牌时）
- 突发量受桶容量和 Semaphore 双重约束
