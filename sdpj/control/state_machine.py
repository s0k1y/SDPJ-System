"""StateScheduler 状态机定义"""
from statemachine import StateMachine, State


class SystemStateMachine(StateMachine):
    """系统状态机"""

    # 定义状态
    idle = State('空闲', initial=True)
    detecting = State('检测中')
    generating_report = State('生成报告中')
    error = State('异常')

    # 定义转移
    start_detection = idle.to(detecting)
    detection_done = detecting.to(generating_report)
    report_done = generating_report.to(idle)
    to_error = idle.to(error) | detecting.to(error) | generating_report.to(error)
    recover = error.to(idle)

    def trigger_error(self):
        """触发错误转移"""
        self.to_error()
