"""DI 依赖注入 — 组合根"""
from sdpj.bootstrap import build_scheduler
from sdpj.control.state_scheduler_interface import StateSchedulerInterface


def get_scheduler() -> StateSchedulerInterface:
    return build_scheduler()
