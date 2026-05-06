## ADDED Requirements

### Requirement: CLI 用户列表命令
CLI SHALL 提供 `sdpj user list` 命令，调用 `scheduler.list_all_users()` 并以表格形式展示所有用户的 ID、用户名和创建时间。

#### Scenario: 列出所有用户
- **WHEN** 用户执行 `sdpj user list`
- **THEN** CLI SHALL 调用 `scheduler.list_all_users()` 并以表格形式展示用户列表

#### Scenario: 无用户时提示
- **WHEN** 用户执行 `sdpj user list` 且系统中无用户
- **THEN** CLI SHALL 显示"暂无用户"

### Requirement: CLI 管理员删除用户命令
CLI SHALL 提供 `sdpj user delete-user` 命令，接收 `--user-id` 参数，调用 `scheduler.schedule_account_operation("admin_delete_user", {"user_id": ...})`。

#### Scenario: 管理员删除用户
- **WHEN** 用户执行 `sdpj user delete-user --user-id 3` 并确认
- **THEN** CLI SHALL 调用 `scheduler.schedule_account_operation("admin_delete_user", {"user_id": 3})` 并显示操作结果

#### Scenario: 删除用户需确认
- **WHEN** 用户执行 `sdpj user delete-user --user-id 3`
- **THEN** CLI SHALL 要求用户确认操作

### Requirement: CLI 更新用户资料命令
CLI SHALL 提供 `sdpj user update-profile` 命令，接收 `--username` 参数，调用 `scheduler.schedule_account_operation("update_profile", {"user_id": ..., "username": ...})`。

#### Scenario: 更新用户名
- **WHEN** 用户执行 `sdpj user update-profile --username newname` 且已登录（user_id=5）
- **THEN** CLI SHALL 调用 `scheduler.schedule_account_operation("update_profile", {"user_id": 5, "username": "newname"})` 并显示操作结果

#### Scenario: 缺少用户名参数报错
- **WHEN** 用户执行 `sdpj user update-profile` 不带 `--username`
- **THEN** CLI SHALL 报错提示 `--username` 为必填参数
