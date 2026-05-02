"""Wave 3 StateScheduler 集成测试"""
import pytest


class TestStateSchedulerIntegration:
    """StateScheduler 集成测试"""

    def test_state_scheduler_import(self):
        """测试 StateScheduler 导入"""
        from sdpj.control.state_scheduler import StateScheduler
        scheduler = StateScheduler()
        assert scheduler is not None

    def test_state_machine_initial_state(self):
        """测试状态机初始状态"""
        from sdpj.control.state_scheduler import StateScheduler
        scheduler = StateScheduler()
        assert scheduler.get_system_state() == "idle"

    def test_state_transitions(self):
        """测试状态转移"""
        from sdpj.control.state_scheduler import StateScheduler
        scheduler = StateScheduler()
        
        # idle -> detecting
        scheduler.state_machine.start_detection()
        assert scheduler.get_system_state() == "detecting"
        
        # detecting -> generating_report
        scheduler.state_machine.detection_done()
        assert scheduler.get_system_state() == "generating_report"
        
        # generating_report -> idle
        scheduler.state_machine.report_done()
        assert scheduler.get_system_state() == "idle"

    def test_error_recovery(self):
        """测试异常恢复"""
        from sdpj.control.state_scheduler import StateScheduler
        scheduler = StateScheduler()
        
        # idle -> error
        scheduler.state_machine.trigger_error()
        assert scheduler.get_system_state() == "error"
        
        # error -> idle
        scheduler.state_machine.recover()
        assert scheduler.get_system_state() == "idle"

    def test_all_modules_initialized(self):
        """测试所有模块已初始化"""
        from sdpj.control.state_scheduler import StateScheduler
        scheduler = StateScheduler()
        
        assert scheduler.task_queue is not None
        assert scheduler.event_logger is not None
        assert scheduler.secure_comm is not None
        assert scheduler.detector is not None
        assert scheduler.account_manager is not None
        assert scheduler.dac_manager is not None
        assert scheduler.config_manager is not None
        assert scheduler.report_manager is not None
