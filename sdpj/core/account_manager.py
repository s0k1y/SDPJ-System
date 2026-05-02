"""AccountManager 用户账号管理模块

职责:
1. 用户注册
2. 用户注销
3. 用户登录
4. 维护登录会话与在线态
5. 用户登出
6. 修改当前用户密码
7. 账号切换
8. 查询当前用户资料
9. 列出当前用户拥有的受控资源
"""
from typing import Optional, Dict
from sdpj.drivers.user_center import UserCenter


class AccountManager:
    """用户账号管理模块实现"""

    def __init__(self):
        self.user_center: Optional[UserCenter] = None
        self._sessions: Dict[str, int] = {}  # session_id -> user_id
        self._current_user_id: Optional[int] = None
        self._initialized = False

    async def init(self):
        """初始化"""
        if not self._initialized:
            from sdpj.infrastructure.database.user_db import UserDB, UserDBSessionManager
            from sdpj.infrastructure.utils.utils_lib import UtilsLib

            session_manager = UserDBSessionManager("sqlite+aiosqlite:///./data/db/user.db")
            user_db = UserDB(session_manager)
            utils_lib = UtilsLib()
            self.user_center = UserCenter(user_db, utils_lib)
            self._initialized = True

    async def register(self, username: str, password: str) -> tuple[bool, str]:
        """用户注册

        Args:
            username: 账号
            password: 明文密码

        Returns:
            (成功标志, 错误信息或用户ID)
        """
        # 账号格式校验
        if not username or len(username) < 3:
            return False, "账号长度至少3个字符"

        # 密码强度校验
        if not password or len(password) < 6:
            return False, "密码长度至少6个字符"

        try:
            user_id = await self.user_center.register_user(username, password)
            return True, f"注册成功，用户ID: {user_id}"
        except Exception as e:
            return False, f"注册失败: {str(e)}"

    async def unregister(self, user_id: int) -> tuple[bool, str]:
        """用户注销

        Args:
            user_id: 用户ID

        Returns:
            (成功标志, 错误信息)
        """
        try:
            # 清除该用户的所有会话
            sessions_to_remove = [sid for sid, uid in self._sessions.items() if uid == user_id]
            for sid in sessions_to_remove:
                del self._sessions[sid]

            # 如果是当前用户,清除当前用户状态
            if self._current_user_id == user_id:
                self._current_user_id = None

            # 调用下层注销
            success = await self.user_center.delete_user(user_id)
            if success:
                return True, ""
            else:
                return False, "注销失败"
        except Exception as e:
            return False, str(e)

    async def login(self, username: str, password: str) -> tuple[bool, str | None]:
        """用户登录

        Args:
            username: 账号
            password: 明文密码

        Returns:
            (成功标志, session_id或None)
        """
        try:
            user_id = await self.user_center.verify_credentials(username, password)
            if user_id:
                # 生成session_id
                import uuid
                session_id = str(uuid.uuid4())
                self._sessions[session_id] = user_id
                self._current_user_id = user_id
                return True, session_id
            else:
                return False, None
        except Exception as e:
            return False, None

    def logout(self, session_id: str) -> bool:
        """用户登出

        Args:
            session_id: 会话ID

        Returns:
            成功标志
        """
        if session_id in self._sessions:
            user_id = self._sessions[session_id]
            del self._sessions[session_id]

            # 如果是当前用户,清除当前用户状态
            if self._current_user_id == user_id:
                self._current_user_id = None

            return True
        return False

    def get_current_session(self) -> Optional[int]:
        """维护登录会话与在线态 - 获取当前登录用户ID

        Returns:
            当前登录用户ID或None
        """
        return self._current_user_id

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
        """修改当前用户密码

        Args:
            user_id: 用户ID
            old_password: 原明文密码
            new_password: 新明文密码

        Returns:
            (成功标志, 错误信息)
        """
        # 新密码强度校验
        if not new_password or len(new_password) < 6:
            return False, "新密码长度至少6个字符"

        try:
            # 获取用户信息验证原密码
            user = await self.user_center.get_user_by_id(user_id)
            if not user:
                return False, "用户不存在"

            # 验证原密码
            verified_user_id = await self.user_center.verify_credentials(user['username'], old_password)
            if not verified_user_id:
                return False, "原密码不正确"

            # 更新密码
            success = await self.user_center.update_user_password(user_id, new_password)
            if success:
                return True, ""
            else:
                return False, "密码更新失败"
        except Exception as e:
            return False, str(e)

    async def switch_account(self, username: str, password: str) -> tuple[bool, str | None]:
        """账号切换

        Args:
            username: 目标账号
            password: 明文密码

        Returns:
            (成功标志, 新session_id或None)
        """
        # 清除当前会话
        if self._current_user_id:
            sessions_to_remove = [sid for sid, uid in self._sessions.items() if uid == self._current_user_id]
            for sid in sessions_to_remove:
                del self._sessions[sid]

        # 登录新账号
        return await self.login(username, password)

    async def get_current_user_profile(self) -> Optional[dict]:
        """查询当前用户资料

        Returns:
            用户资料(用户ID、账号)或None
        """
        if not self._current_user_id:
            return None

        return await self.user_center.get_user_by_id(self._current_user_id)

    async def list_user_resources(self, user_id: Optional[int] = None) -> list[dict]:
        """列出当前用户拥有的受控资源

        Args:
            user_id: 用户ID,如果为None则使用当前登录用户

        Returns:
            资源列表(每条含资源ID、资源类型)
        """
        target_user_id = user_id if user_id is not None else self._current_user_id
        if not target_user_id:
            return []

        return await self.user_center.get_resources_by_owner(target_user_id)
