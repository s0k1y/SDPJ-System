## Context

CLI 模块（`sdpj/ui/cli/`）是用户交互入口之一，通过 `StateSchedulerInterface` 与系统交互。后端 StateScheduler 经历了以下变更：

1. **接口签名变更**：`query_dataset_detail` 和 `export_dataset_file` 新增了 `user_id` 参数用于 DAC 校验，但接口文件未同步更新
2. **操作参数变更**：`schedule_dac_operation` 的 `grant` 操作从 `target_user_id` 改为 `target_username`；`remove_adapter` 的 `resource_id` 变为必填
3. **返回结构变更**：`query_detection_progress` 返回值从扁平队列变为分组结构（groups）
4. **新增操作**：`list_all_users`、`admin_delete_user`、`update_profile` 等后端已支持但 CLI 未暴露
5. **账号操作缺少 user_id**：`profile`、`change_password`、`list_resources` 等操作未传递当前登录用户 ID

当前 CLI 代码与后端存在 5 处调用不匹配（会导致运行时错误）和 3 处功能缺失。

## Goals / Non-Goals

**Goals:**
- 修复所有 CLI 与 StateScheduler 之间的接口调用不匹配问题
- 修复所有参数传递错误（user_id 缺失、参数名不一致等）
- 修复 `detect progress` 输出格式以适配新的分组返回结构
- 新增 CLI 命令暴露后端已有能力（list-users、admin-delete-user、update-profile）
- 同步更新 `state_scheduler_interface.py` 中过时的接口签名
- 改进 `logs` 命令支持分页

**Non-Goals:**
- 不重构 CLI 的整体架构（仍使用 Click 框架和现有目录结构）
- 不新增后端功能（仅适配现有后端接口）
- 不修改 WebUI 后端路由
- 不修改 StateScheduler 的实现逻辑

## Decisions

### D1: 接口文件同步策略

**决策**: 直接更新 `state_scheduler_interface.py` 中 `query_dataset_detail` 和 `export_dataset_file` 的签名，添加 `user_id: int | None = None` 参数。

**理由**: 接口文件应与实现保持一致。`user_id` 为可选参数（`None`），不破坏现有调用方。

**替代方案**: 在 CLI 端做适配层 — 被否决，因为接口不一致是根本问题，应在接口层修复。

### D2: detect progress 输出格式

**决策**: 重写 `detect progress` 命令，按分组结构渲染：每个任务组显示模型名、整体状态、进度统计和子任务列表。

**理由**: 后端 `query_detection_progress` 已返回 `groups` 结构，包含 `model_name`、`status`、`progress`、`children` 等字段，CLI 应完整呈现这些信息。

**替代方案**: 仅显示扁平列表 — 被否决，因为会丢失任务组归属关系和模型名信息。

### D3: DAC grant 命令参数

**决策**: 将 `--target-user` 选项从 `type=int` 改为 `type=str`，参数名改为 `--target-username`，传递 `target_username` 而非 `target_user_id`。

**理由**: 后端 `DACManager.grant_access` 接收 `target_username`（字符串），而非 `target_user_id`（整数）。

### D4: remove_adapter 命令

**决策**: 将 `--resource-id` 从可选参数改为必填参数。

**理由**: 后端 `schedule_private_resource_operation` 的 `remove_adapter` 操作要求 `resource_id` 必填，否则返回错误。

### D5: 新增命令的组织方式

**决策**: 
- `user list` 作为 `user_group` 的子命令
- `user delete-user` 作为 `user_group` 的子命令（需登录，管理员功能）
- `user update-profile` 作为 `user_group` 的子命令

**理由**: 遵循现有 CLI 命令组织方式，用户管理相关命令统一放在 `user` 组下。

### D6: query_available_datasets 的 user_id 处理

**决策**: 使用当前登录用户的 `user_id` 替代硬编码的 `0`。

**理由**: `user_id=0` 绕过了 DAC 过滤，导致私有数据集的访问控制失效。应使用实际登录用户 ID 以正确过滤无权访问的私有数据集。

## Risks / Trade-offs

- **[BREAKING: 参数变更]** `user auth grant` 的 `--target-user` 从整数改为字符串 → 在帮助文本中明确说明
- **[BREAKING: 必填参数]** `config remove-adapter` 的 `--resource-id` 变为必填 → 在帮助文本中明确说明
- **[兼容性]** 接口文件签名变更可能影响其他调用方 → `user_id` 参数为可选（默认 `None`），不破坏现有调用
- **[输出格式]** `detect progress` 输出格式变更可能影响脚本解析 → 这是必要的适配，旧格式已无法正确渲染
