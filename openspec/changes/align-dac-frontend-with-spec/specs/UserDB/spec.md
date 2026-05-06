## MODIFIED Requirements

### Requirement: 用户表结构
用户表 SHALL 遵循 3NF 定义：用户(用户ID[主键], 账号, 密码)，不包含角色字段。

#### Scenario: 创建用户时不包含角色
- **WHEN** 系统创建新用户
- **THEN** 用户记录仅包含 user_id、username、password、created_at 字段，不包含 role 字段

#### Scenario: 查询用户时不返回角色
- **WHEN** 系统查询用户信息
- **THEN** 返回的用户数据不包含 role 字段

## REMOVED Requirements

### Requirement: 用户角色字段
**Reason**: 规格文档 `UserDB.md` 明确定义用户表为 `用户(用户ID[主键], 账号, 密码)`，不包含角色字段。角色概念在系统规格中不存在，自主访问控制通过ACL实现而非角色。
**Migration**: 删除 User 模型的 `role` 字段，删除数据库 User 表的 `role` 列，删除 `update_role` 相关代码。

### Requirement: 用户角色更新
**Reason**: 规格文档未定义角色管理功能，AccountManager 的职责不包含角色更新。
**Migration**: 删除 `admin_update_role` 操作及其在 StateScheduler、AccountManager、UserCenter、UserDB、UserRepository 中的调用链。
