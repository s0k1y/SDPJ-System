## Why

后端 StateScheduler 经历了大量改动（接口签名变更、新增操作、返回结构变化），CLI 仍停留在旧版接口调用方式上，导致多个命令存在参数不匹配、输出格式错误、功能缺失等问题。CLI 作为用户交互入口，必须与后端接口保持一致，否则无法正常使用。

## What Changes

- **BREAKING** 修复 `query_dataset_detail` 和 `export_dataset_file` 接口签名不匹配：接口文件缺少 `user_id` 参数，CLI 调用方式与实现不一致
- **BREAKING** 修复 `schedule_account_operation` 中 `profile`、`change_password`、`list_resources` 等操作未传递 `user_id` 的问题
- **BREAKING** 修复 `schedule_dac_operation` 的 `grant` 操作：CLI 传递 `target_user_id`，但后端实际接收 `target_username`
- **BREAKING** 修复 `remove_adapter` 命令：`resource_id` 在后端为必填参数，CLI 中为可选
- **BREAKING** 修复 `detect progress` 命令输出格式：后端 `query_detection_progress` 已返回分组结构（groups），CLI 仍按旧的扁平队列格式渲染
- 修复 `detect datasets` 命令：使用 `user_id=0` 绕过 DAC 过滤，应使用当前登录用户 ID
- 新增 `user list` 命令：暴露后端 `list_all_users` 能力
- 新增 `user delete-user` 管理员命令：暴露后端 `admin_delete_user` 操作
- 新增 `user update-profile` 命令：暴露后端 `update_profile` 操作
- 改进 `logs` 命令：支持分页参数（`--page`、`--page-size`）
- 改进 `watch`/`watch-errors` 命令：使用异步轮询替代同步阻塞

## Capabilities

### New Capabilities

- `cli-user-management-extended`: 扩展 CLI 用户管理命令（list-users、admin-delete-user、update-profile）

### Modified Capabilities

- `CLI`: 修复接口调用不匹配、参数传递错误、输出格式过时等问题，使 CLI 与当前后端 StateScheduler 接口保持一致

## Impact

- **受影响代码**: `sdpj/ui/cli/` 目录下所有命令文件（detect.py、report.py、user.py、adapter.py）和主入口 main.py
- **受影响接口**: `sdpj/control/state_scheduler_interface.py` 中 `query_dataset_detail` 和 `export_dataset_file` 签名需更新
- **依赖**: 无新增外部依赖，仅修复与现有 StateScheduler 的调用适配
- **风险**: 部分命令参数为 BREAKING 变更，已有使用习惯需调整
