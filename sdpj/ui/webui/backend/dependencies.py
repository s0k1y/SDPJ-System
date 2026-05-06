"""DI 依赖注入 — 组合根"""
from sdpj.bootstrap import build_scheduler
from sdpj.control.state_scheduler_interface import StateSchedulerInterface

_scheduler: StateSchedulerInterface | None = None


def get_scheduler() -> StateSchedulerInterface:
    global _scheduler
    if _scheduler is None:
        _scheduler = build_scheduler()
    return _scheduler
