"""StateScheduler 系统状态管理及调度控制"""
from sdpj.core.task_queue_manager_interface import TaskQueueManagerInterface
from sdpj.core.event_logger_interface import EventLoggerInterface
from sdpj.core.secure_comm_manager_interface import SecureCommManagerInterface
from sdpj.core.sdpj_detector_interface import SDPJDetectorInterface
from sdpj.core.account_manager_interface import AccountManagerInterface
from sdpj.core.dac_manager_interface import DACManagerInterface
from sdpj.core.private_config_manager_interface import PrivateConfigManagerInterface
from sdpj.core.report_manager_interface import ReportManagerInterface
from sdpj.core.task_queue_manager import TaskQueueManager
from sdpj.core.event_logger import EventLogger
from sdpj.core.secure_comm_manager import SecureCommManager
from sdpj.core.sdpj_detector import SDPJDetector
from sdpj.core.account_manager import AccountManager
from sdpj.core.dac_manager import DACManager
from sdpj.core.private_config_manager import PrivateConfigManager
from sdpj.core.report_manager import ReportManager
from .state_machine import SystemStateMachine


class StateScheduler:
    """系统状态管理及调度控制"""

    def __init__(
        self,
        task_queue: TaskQueueManagerInterface | None = None,
        event_logger: EventLoggerInterface | None = None,
        secure_comm: SecureCommManagerInterface | None = None,
        detector: SDPJDetectorInterface | None = None,
        account_manager: AccountManagerInterface | None = None,
        dac_manager: DACManagerInterface | None = None,
        config_manager: PrivateConfigManagerInterface | None = None,
        report_manager: ReportManagerInterface | None = None
    ):
        """初始化StateScheduler

        Args:
            task_queue: 任务队列管理器接口(可选,用于依赖注入)
            event_logger: 事件日志管理器接口(可选,用于依赖注入)
            secure_comm: 安全通信管理器接口(可选,用于依赖注入)
            detector: SDPJ检测器接口(可选,用于依赖注入)
            account_manager: 账号管理器接口(可选,用于依赖注入)
            dac_manager: DAC管理器接口(可选,用于依赖注入)
            config_manager: 配置管理器接口(可选,用于依赖注入)
            report_manager: 报告管理器接口(可选,用于依赖注入)
        """
        # Wave 0 基础设施层
        self.task_queue = task_queue if task_queue is not None else TaskQueueManager()
        self.event_logger = event_logger if event_logger is not None else EventLogger()
        self.secure_comm = secure_comm if secure_comm is not None else SecureCommManager()

        # Wave 2 执行逻辑层
        self.detector = detector if detector is not None else SDPJDetector()
        self.account_manager = account_manager if account_manager is not None else AccountManager()
        self.dac_manager = dac_manager if dac_manager is not None else DACManager()
        self.config_manager = config_manager if config_manager is not None else PrivateConfigManager()
        self.report_manager = report_manager if report_manager is not None else ReportManager()

        # 状态机
        self.state_machine = SystemStateMachine()
        self._initialized = False

    async def init(self):
        """初始化所有模块"""
        if not self._initialized:
            await self.detector.init()
            await self.account_manager.init()
            await self.dac_manager.init()
            await self.config_manager.init()
            await self.report_manager.init()
            self._initialized = True

    # ==================== 检测调度 ====================

    async def start_detection(self, user_id: int, config_data: dict) -> dict:
        """接收并解析检测启动指令并下发为可执行任务组"""
        try:
            self.state_machine.start_detection()
            
            # 创建任务组
            model_id = config_data.get("model_id")
            dataset_id = config_data.get("dataset_id")
            
            # 入队任务
            task_desc = {
                "user_id": user_id,
                "model_id": model_id,
                "dataset_id": dataset_id,
                "algorithm_type": config_data.get("algorithm_type", "static")
            }
            task_id = await self.task_queue.enqueue_task(task_desc)
            
            # 记录日志
            await self.event_logger.log_user_operation(
                user_id, "start_detection", {"task_id": task_id}
            )
            
            return {"success": True, "task_id": task_id}
        except Exception as e:
            self.state_machine.trigger_error()
            await self.event_logger.log_error("StateScheduler", "DetectionError", str(e))
            return {"success": False, "error": str(e)}

    async def execute_detection_task(self, task_id: str) -> dict:
        """调度执行单个检测子任务"""
        try:
            # 出队任务
            task = await self.task_queue.dequeue_task()
            if not task:
                return {"success": False, "error": "No task available"}
            
            # 更新状态
            await self.task_queue.update_task_status(task_id, "进行中")
            
            # 执行检测（简化实现）
            # result = await self.detector.static_detect(...)
            
            # 更新状态
            await self.task_queue.update_task_status(task_id, "已完成")
            
            self.state_machine.detection_done()
            return {"success": True}
        except Exception as e:
            self.state_machine.trigger_error()
            return {"success": False, "error": str(e)}

    async def query_detection_progress(self, task_id: str) -> dict:
        """查询检测任务执行进度"""
        status = await self.task_queue.query_task_status(task_id)
        return {"task_id": task_id, "status": status}

    # ==================== 报告管理 ====================

    async def generate_report(self, task_group_id: int) -> dict:
        """生成检测报告"""
        try:
            self.state_machine.report_done()
            report = await self.report_manager.generate_static_report(task_group_id)
            return {"success": True, "report": report}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 用户管理 ====================

    async def register_user(self, username: str, password: str) -> dict:
        """调度用户注册"""
        # 解密（WebUI 模式）
        decrypted_password = self.secure_comm.decrypt_credentials(password.encode()) if isinstance(password, str) and len(password) > 50 else password
        
        success, msg = await self.account_manager.register(username, decrypted_password)
        
        if success:
            await self.event_logger.log_user_operation(0, "register", {"username": username})
        
        return {"success": success, "message": msg}

    async def login_user(self, username: str, password: str) -> dict:
        """调度用户登录"""
        decrypted_password = self.secure_comm.decrypt_credentials(password.encode()) if isinstance(password, str) and len(password) > 50 else password
        
        success, session_id = await self.account_manager.login(username, decrypted_password)
        
        if success:
            await self.event_logger.log_user_operation(0, "login", {"username": username})
        
        return {"success": success, "session_id": session_id}

    # ==================== 状态查询 ====================

    def get_system_state(self) -> str:
        """获取当前系统状态"""
        return self.state_machine.current_state_value

    async def query_logs(self, filters: dict) -> list:
        """查询系统日志"""
        return await self.event_logger.query_logs(filters)
