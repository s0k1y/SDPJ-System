## MODIFIED Requirements

### Requirement: CLI 检测命令与 StateScheduler 接口一致
CLI 的检测相关命令（detect start、detect datasets、detect progress、detect dataset-detail、detect dataset-export）SHALL 使用与 StateScheduler 实现一致的接口签名和参数传递方式。

#### Scenario: detect datasets 使用当前登录用户 ID
- **WHEN** 用户执行 `sdpj detect datasets` 且已登录（user_id=5）
- **THEN** CLI SHALL 调用 `scheduler.query_available_datasets(user_id=5)` 而非 `user_id=0`

#### Scenario: detect progress 按分组结构渲染
- **WHEN** 用户执行 `sdpj detect progress` 且后端返回分组结构 `{"success": True, "groups": [...]}`
- **THEN** CLI SHALL 按任务组渲染输出，每组显示模型名、整体状态、进度统计和子任务列表

#### Scenario: detect dataset-detail 传递 user_id
- **WHEN** 用户执行 `sdpj detect dataset-detail 3` 且已登录（user_id=5）
- **THEN** CLI SHALL 调用 `scheduler.query_dataset_detail(3, user_id=5)`

#### Scenario: detect dataset-export 传递 user_id
- **WHEN** 用户执行 `sdpj detect dataset-export 3` 且已登录（user_id=5）
- **THEN** CLI SHALL 调用 `scheduler.export_dataset_file(3, user_id=5)`

### Requirement: CLI 账号操作传递当前用户 ID
CLI 的账号管理命令（profile、change_password、list_resources）SHALL 在调用 `schedule_account_operation` 时传递当前登录用户的 `user_id`。

#### Scenario: profile 命令传递 user_id
- **WHEN** 用户执行 `sdpj user profile` 且已登录（user_id=5）
- **THEN** CLI SHALL 调用 `scheduler.schedule_account_operation("get_profile", {"user_id": 5})`

#### Scenario: change_password 命令传递 user_id
- **WHEN** 用户执行 `sdpj user password` 且已登录（user_id=5）
- **THEN** CLI SHALL 调用 `scheduler.schedule_account_operation("change_password", {"user_id": 5, "old_password": ..., "new_password": ...})`

#### Scenario: list_resources 命令传递 user_id
- **WHEN** 用户执行 `sdpj user resources` 且已登录（user_id=5）
- **THEN** CLI SHALL 调用 `scheduler.schedule_account_operation("list_resources", {"user_id": 5})`

### Requirement: CLI DAC 授权命令使用 target_username
CLI 的 `user auth grant` 命令 SHALL 接收 `--target-username`（字符串）参数，并传递 `target_username` 而非 `target_user_id`。

#### Scenario: grant 命令使用用户名授权
- **WHEN** 用户执行 `sdpj user auth grant --resource-id 10 --target-username alice`
- **THEN** CLI SHALL 调用 `scheduler.schedule_dac_operation("grant", {"resource_id": 10, "target_username": "alice", "caller_user_id": ...})`

### Requirement: CLI remove-adapter 命令要求必填 resource-id
CLI 的 `config remove-adapter` 命令 SHALL 将 `--resource-id` 设为必填参数。

#### Scenario: remove-adapter 缺少 resource-id 报错
- **WHEN** 用户执行 `sdpj config remove-adapter --model-id gpt4` 但未提供 `--resource-id`
- **THEN** CLI SHALL 报错提示 `--resource-id` 为必填参数

#### Scenario: remove-adapter 传递 resource-id 成功
- **WHEN** 用户执行 `sdpj config remove-adapter --model-id gpt4 --resource-id 10`
- **THEN** CLI SHALL 调用 `scheduler.schedule_private_resource_operation("remove_adapter", {"user_id": ..., "model_id": "gpt4", "resource_id": 10})`

### Requirement: StateSchedulerInterface 签名与实现一致
`state_scheduler_interface.py` 中 `query_dataset_detail` 和 `export_dataset_file` 的签名 SHALL 包含 `user_id: int | None = None` 参数，与 StateScheduler 实现保持一致。

#### Scenario: query_dataset_detail 接口签名
- **WHEN** 查看 `StateSchedulerInterface.query_dataset_detail` 的签名
- **THEN** 其签名 SHALL 为 `async def query_dataset_detail(self, dataset_id: int, user_id: int | None = None) -> dict | None`

#### Scenario: export_dataset_file 接口签名
- **WHEN** 查看 `StateSchedulerInterface.export_dataset_file` 的签名
- **THEN** 其签名 SHALL 为 `async def export_dataset_file(self, dataset_id: int, user_id: int | None = None) -> dict | None`

### Requirement: CLI logs 命令支持分页
CLI 的 `logs` 命令 SHALL 支持 `--page` 和 `--page-size` 选项用于分页查询。

#### Scenario: 使用分页参数查询日志
- **WHEN** 用户执行 `sdpj logs --page 2 --page-size 20`
- **THEN** CLI SHALL 调用 `scheduler.query_logs({"page": 2, "page_size": 20})`

#### Scenario: 不使用分页参数查询日志
- **WHEN** 用户执行 `sdpj logs` 不带分页参数
- **THEN** CLI SHALL 调用 `scheduler.query_logs(None)` 并显示全部结果
