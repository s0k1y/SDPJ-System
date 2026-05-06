## Context

当前前端 `DacManager.vue` 实现的是"用户管理"功能（用户列表、角色编辑、用户删除），与规格文档 `6.模块职责细化及技术细节/3.Execution Logic Layer/DACManager.md` 中定义的"自主访问控制管理"功能完全不同。

后端核心层（DACManager + StateScheduler + UserCenter + UserDB）已正确实现规格定义的4项DAC能力（授予/移除/判定/查询），后端API端点（`POST /api/users/dac`、`GET /api/users/dac/check`）也已就绪，但前端完全没有调用这些端点。

此外，当前代码中存在规格未定义的"角色"概念（admin/user/viewer），包括 User 模型的 `role` 字段、`admin_update_role` 操作、前端角色编辑功能等，这些都需要清理。

## Goals / Non-Goals

**Goals:**
- 重写 `DacManager.vue` 为自主访问控制管理页面，对齐规格文档定义的4项DAC功能
- 前端调用已有的 `POST /api/users/dac`（grant/revoke/list）和 `GET /api/users/dac/check` 端点
- 移除规格中不存在的"角色"概念相关代码（模型字段、API端点、前端功能）
- 清理 `app.py` 中偏离规格的 `/api/dac/users` 相关端点

**Non-Goals:**
- 不修改后端核心层（DACManager、StateScheduler、UserCenter、UserDB）的已正确实现的DAC逻辑
- 不实现权限委托机制（规格明确排除）
- 不实现权限变更日志（由 EventLogger 完成，不在本次变更范围）
- 不新增后端DAC端点（已有端点足够支撑前端需求）

## Decisions

### 1. 前端页面结构：资源列表 + 授权管理

**决策**：DacManager.vue 采用"我的资源列表 → 选中资源 → 查看授权清单 → 授予/移除访问权"的交互模式。

**理由**：规格定义的DAC操作都以"资源"为核心对象（资源ID为输入），用户需要先选择一个自己拥有的资源，才能查看和管理该资源的访问控制。这符合自主访问控制的语义——资源拥有者自主决定谁可以访问。

**替代方案**：直接展示所有ACL条目的扁平列表 → 否决，因为用户可能拥有多个资源，扁平列表缺乏资源维度的组织，且规格要求"资源拥有者查看其资源当前的授权状况"。

### 2. 移除角色概念：数据库迁移策略

**决策**：删除 User 模型的 `role` 字段，通过 `_migrate_schema` 的反向操作（重建不含 role 列的 User 表）完成迁移。

**理由**：规格文档 `UserDB.md` 明确定义用户表为 `用户(用户ID[主键], 账号, 密码)`，不包含角色字段。角色概念在规格中不存在，保留会引入混淆。

**替代方案**：保留 role 字段但不在前端暴露 → 否决，因为保留规格外字段会持续造成模型与规格不一致，违反规范合规性要求。

### 3. 清理偏离规格的API端点

**决策**：移除 `app.py` 中的 `/api/dac/users`、`/api/dac/users/{user_id}` (DELETE/PUT) 三个端点。用户列表功能如需保留，应通过 `/api/users/account` (operation=list_users) 实现，但本次变更不新增该功能。

**理由**：这些端点将用户CRUD操作错误地放在了 `/api/dac/` 路径下，违反了规格中DAC模块的职责边界。DAC模块只负责资源访问控制，不负责用户管理。

## Risks / Trade-offs

- [风险] 删除 role 字段后，已有用户数据中的 role 值丢失 → 缓解：当前系统处于初始化阶段，role 字段未被任何规格定义的功能使用，无业务影响
- [风险] 移除 `/api/dac/users` 端点后，如果其他前端页面依赖该端点会报错 → 缓解：已确认只有 DacManager.vue 调用该端点，重写后将不再依赖
- [风险] 前端重写后用户交互流程变化较大 → 缓解：当前系统处于初始化阶段，无存量用户需要适应变化

## Migration Plan

1. 先移除后端偏离规格的代码（端点、role相关逻辑）
2. 执行数据库迁移（删除 role 列）
3. 重写前端 DacManager.vue
4. 端到端验证：登录 → 查看资源列表 → 选中资源 → 查看授权清单 → 授予访问权 → 移除访问权

## Open Questions

- 无
