"""系统状态头文件 — 预设定系统的全部状态与转移规则

对应 StateScheduler.md 技术细节 1.1:
"通过预设定好的系统状态头文件规定系统的状态"

所有状态定义集中于此，StateScheduler 导入 SystemStateMachine 来跟踪系统当前状态。
"""

from statemachine import State, StateMachine


class SystemStateMachine(StateMachine):
    """系统有限状态机

    状态:
        idle            — 空闲，系统就绪
        detecting       — 检测中，正在执行检测任务
        generating_report — 生成报告中
        error           — 异常，需要恢复

    转移:
        idle → detecting          (start_detection)
        detecting → idle          (detection_done)
        idle → generating_report  (start_report)
        generating_report → idle  (report_done)
        any → error               (to_error)
        error → idle              (recover)
    """

    idle = State("空闲", initial=True)
    detecting = State("检测中")
    generating_report = State("生成报告中")
    configuring = State("配置管理中")
    error = State("异常")

    start_detection = idle.to(detecting)
    detection_done = detecting.to(idle)
    start_report = idle.to(generating_report)
    report_done = generating_report.to(idle)
    start_configuring = idle.to(configuring)
    configuring_done = configuring.to(idle)
    to_error = (
        idle.to(error) | detecting.to(error) | generating_report.to(error) | configuring.to(error)
    )
    recover = error.to(idle)


# ── 状态标识常量 (供外部查询比对) ──

STATE_IDLE = "idle"
STATE_DETECTING = "detecting"
STATE_GENERATING_REPORT = "generating_report"
STATE_CONFIGURING = "configuring"
STATE_ERROR = "error"

ALL_STATES = [STATE_IDLE, STATE_DETECTING, STATE_GENERATING_REPORT, STATE_CONFIGURING, STATE_ERROR]
