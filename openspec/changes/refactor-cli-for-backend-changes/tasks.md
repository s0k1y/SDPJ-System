## 1. 接口文件修复

- [x] 1.1 更新 `state_scheduler_interface.py` 中 `query_dataset_detail` 签名，添加 `user_id: int | None = None` 参数
- [x] 1.2 更新 `state_scheduler_interface.py` 中 `export_dataset_file` 签名，添加 `user_id: int | None = None` 参数

## 2. 检测命令修复 (detect.py)

- [x] 2.1 修复 `detect datasets` 命令：使用当前登录用户 ID 替代 `user_id=0`
- [x] 2.2 重写 `detect progress` 命令：按分组结构渲染输出（模型名、整体状态、进度统计、子任务列表）
- [x] 2.3 修复 `detect dataset-detail` 命令：传递 `user_id` 参数
- [x] 2.4 修复 `detect dataset-export` 命令：传递 `user_id` 参数

## 3. 用户命令修复 (user.py)

- [x] 3.1 修复 `user profile` 命令：传递 `user_id` 到 `schedule_account_operation`
- [x] 3.2 修复 `user password` 命令：传递 `user_id` 到 `schedule_account_operation`
- [x] 3.3 修复 `user resources` 命令：传递 `user_id` 到 `schedule_account_operation`
- [x] 3.4 修复 `user auth grant` 命令：将 `--target-user`(int) 改为 `--target-username`(str)，传递 `target_username`

## 4. 配置命令修复 (adapter.py)

- [x] 4.1 修复 `config remove-adapter` 命令：将 `--resource-id` 从可选改为必填

## 5. 新增用户管理命令 (user.py)

- [x] 5.1 新增 `user list` 命令：调用 `scheduler.list_all_users()` 并以表格展示
- [x] 5.2 新增 `user delete-user` 命令：调用 `scheduler.schedule_account_operation("admin_delete_user", ...)`，需确认
- [x] 5.3 新增 `user update-profile` 命令：调用 `scheduler.schedule_account_operation("update_profile", ...)`

## 6. 日志命令改进 (main.py)

- [x] 6.1 为 `logs` 命令添加 `--page` 和 `--page-size` 分页选项

## 7. 验证

- [x] 7.1 运行项目确保 CLI 可正常导入和启动
- [x] 7.2 验证所有修改的命令参数传递正确
