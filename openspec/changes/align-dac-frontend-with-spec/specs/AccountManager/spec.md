## REMOVED Requirements

### Requirement: 管理员更新用户角色
**Reason**: 规格文档 `AccountManager.md` 未定义角色管理功能。AccountManager 的职责为账号注册/注销、登录/会话维护、密码修改、用户资料查询，不包含角色管理。自主访问控制通过 DACManager 的 ACL 机制实现，而非角色。
**Migration**: 删除 `admin_update_role` 操作，删除 StateScheduler 中的 `_op_admin_update_role` 方法和 dispatch 表项，删除前端角色编辑功能。
