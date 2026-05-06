## Why

前端 DacManager.vue 当前实现的是"用户管理"功能（用户列表、角色编辑、用户删除），与规格文档中定义的"自主访问控制管理"功能完全不同。规格文档明确 DACManager 负责资源级读权限的授予/移除/判定/查询，后端核心层（DACManager + StateScheduler）已正确实现，但前端页面和部分后端API端点偏离了规格。需要将前端对齐到规格定义的DAC功能，同时清理规格中不存在的"角色"概念相关代码。

## What Changes

- **BREAKING** 重写 `DacManager.vue`：从"用户管理"页面改为"自主访问控制管理"页面，实现资源访问权的授予、移除、查询功能
- **BREAKING** 移除规格中不存在的"角色"概念：删除 `User` 模型中的 `role` 字段、删除 `admin_update_role` 操作、删除前端角色编辑功能
- 清理 `app.py` 中偏离规格的 `/api/dac/users`、`/api/dac/users/{user_id}` 端点（用户CRUD不属于DAC职责）
- 前端新增调用已有的 `POST /api/users/dac`（grant/revoke/list）和 `GET /api/users/dac/check` 端点
- 前端新增资源授权清单展示、授权授予对话框、授权移除操作

## Capabilities

### New Capabilities
- `dac-access-control-ui`: 前端自主访问控制管理界面，包含资源授权清单查询、访问权授予、访问权移除三项交互功能

### Modified Capabilities
- `UserDB`: 移除 User 模型中规格不存在的 `role` 字段，恢复数据库关系模型为 3NF 定义（用户(用户ID[主键], 账号, 密码)）
- `AccountManager`: 移除 `admin_update_role` 操作，角色管理不属于规格定义的AccountManager职责

## Impact

- **前端文件**: `DacManager.vue`（重写）、`Sidebar.vue`（导航标签可能调整）、`api/user.js`（新增DAC调用方法）
- **后端文件**: `app.py`（移除 `/api/dac/users` 等偏离规格端点）、`state_scheduler.py`（移除 `admin_update_role`）、`account_manager.py`（移除 `update_role`）、`user_center.py`（移除 `update_role`）、`user_db.py`（移除 `update_role`）、`user_repo.py`（移除 `update_role`）、`models.py`（移除 `role` 字段）
- **数据库**: 需迁移删除 `User` 表的 `role` 列
- **API**: 移除 `PUT /api/dac/users/{user_id}`、`DELETE /api/dac/users/{user_id}`、`GET /api/dac/users`；前端改为使用 `POST /api/users/dac` 和 `GET /api/users/dac/check`
