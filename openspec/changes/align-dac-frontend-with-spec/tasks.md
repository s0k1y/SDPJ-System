## 1. 后端清理：移除角色概念

- [x] 1.1 删除 `models.py` 中 User 模型的 `role` 字段
- [x] 1.2 删除 `user_repo.py` 中的 `update_role` 方法
- [x] 1.3 删除 `user_db.py` 中的 `update_role` 方法
- [x] 1.4 删除 `user_center.py` 中的 `update_role` 方法
- [x] 1.5 删除 `user_center_interface.py` 中的 `update_role` 接口定义
- [x] 1.6 删除 `account_manager.py` 中的 `update_role_for_user` 方法和 `admin_update_role` 相关逻辑
- [x] 1.7 删除 `account_manager_interface.py` 中的 `update_role_for_user` 接口定义
- [x] 1.8 删除 `state_scheduler.py` 中的 `_op_admin_update_role` 方法和 dispatch 表项
- [x] 1.9 清理 `user_db.py` 的 `get_all_users`、`get_user_by_id` 返回值中移除 `role` 字段
- [x] 1.10 清理 `user_center.py` 的 `get_all_users`、`get_user_by_id` 返回值中移除 `role` 字段
- [x] 1.11 清理 `state_scheduler.py` 的 `list_all_users` 返回值中移除 `role` 字段

## 2. 后端清理：移除偏离规格的API端点

- [x] 2.1 删除 `app.py` 中的 `GET /api/dac/users` 端点
- [x] 2.2 删除 `app.py` 中的 `DELETE /api/dac/users/{user_id}` 端点
- [x] 2.3 删除 `app.py` 中的 `PUT /api/dac/users/{user_id}` 端点

## 3. 数据库迁移

- [x] 3.1 编写迁移脚本删除 User 表的 `role` 列（SQLite 需重建表）
- [x] 3.2 更新 `_migrate_schema` 方法，确保新建数据库不含 role 列

## 4. 前端重写：DacManager.vue

- [x] 4.1 重写 DacManager.vue 模板：资源列表 + 授权清单布局
- [x] 4.2 实现资源列表加载（调用 `GET /api/users/resources`）
- [x] 4.3 实现选中资源后加载授权清单（调用 `POST /api/users/dac` operation=list）
- [x] 4.4 实现访问权授予对话框（输入被授权用户ID，调用 `POST /api/users/dac` operation=grant）
- [x] 4.5 实现访问权移除操作（调用 `POST /api/users/dac` operation=revoke）
- [x] 4.6 实现访问权判定功能（调用 `GET /api/users/dac/check`）
- [x] 4.7 更新 `api/user.js` 新增 DAC 操作的便捷方法（已有，无需修改）

## 5. 验证

- [ ] 5.1 启动应用，登录后进入权限管理页面，验证资源列表展示
- [ ] 5.2 验证选中资源后授权清单展示
- [ ] 5.3 验证授予访问权功能
- [ ] 5.4 验证移除访问权功能
- [ ] 5.5 验证访问权判定功能
- [ ] 5.6 验证无资源/无授权记录时的空状态提示
