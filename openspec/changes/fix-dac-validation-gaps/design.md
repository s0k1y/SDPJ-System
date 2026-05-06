## Context

规格文档 StateScheduler.md 职责16要求在使用私有资源前做 DAC 前置校验。当前代码中，私有配置的 read/update/delete 和私有适配器的 remove 已正确实现 DAC 校验，但私有数据集相关操作和检测启动时的私有配置读取缺失校验。

根本原因是 Dataset 表和 Resource 表之间没有映射关系。对于 PrivateConfig，`config_id = resource_id`（PrivateConfig 表的主键是 Resource 表的外键），天然具备映射。但 Dataset 表在 SampleDB 中，Resource 表在 UserDB 中，两者完全独立，`add_custom_dataset` 注册了 Resource 但丢弃了 `resource_id`。

## Goals / Non-Goals

**Goals:**
- 在 Dataset 表中新增 `resource_id` 列，建立 dataset→resource 映射
- 补齐 StateScheduler 中5处缺失的 DAC 前置校验
- 确保私有数据集的删除/导出/详情查询均经过 DAC 校验
- 确保检测启动时读取私有配置经过 DAC 校验
- 确保数据集列表按用户权限过滤

**Non-Goals:**
- 不修改 DACManager 核心逻辑（已正确实现）
- 不修改 UserCenter/UserDB 的 ACL 操作逻辑
- 不修改前端代码（错误提示由后端统一返回）
- 不重构 Dataset 和 Resource 的关联方式（仅添加 resource_id 列，不改变表间关系架构）

## Decisions

### 1. 在 Dataset 表添加 resource_id 列而非在 Resource 表添加 dataset_id

**决策**：在 SampleDB 的 Dataset 表中新增可空的 `resource_id` 列。

**理由**：
- Resource 表是通用资源表，服务于配置/适配器/数据集等多种资源类型，添加类型特定的外部引用会破坏通用性
- Dataset 表的 `resource_id` 可空，内置数据集为 NULL，私有数据集才有值，语义清晰
- 与 PrivateConfig 的模式一致：PrivateConfig 通过 `config_id = resource_id` 关联，Dataset 通过 `resource_id` 列关联
- 查询方向一致：从业务实体（Dataset）找到资源（Resource），再做 DAC 校验

### 2. 数据集列表权限过滤策略

**决策**：`query_available_datasets` 返回所有内置数据集 + 当前用户拥有的私有数据集 + 通过 ACL 被授权访问的私有数据集。

**理由**：规格要求"用户对私有资源发起使用请求前的前置校验"，列表阶段就应过滤，避免前端展示用户无权访问的数据集。

### 3. start_detection 中私有配置的 DAC 校验

**决策**：在 `start_detection` 中，当 `config_id` 不为空时，先通过 `self._dac.check_access(config_id, user_id)` 校验访问权，拒绝后直接返回错误。

**理由**：与 `schedule_config_operation` 中 read 操作的校验逻辑一致（state_scheduler.py:534-538），保持统一。

## Risks / Trade-offs

- [风险] Dataset 表新增 resource_id 列需要数据库迁移 → 缓解：列可空，不影响现有数据
- [风险] 现有私有数据集的 resource_id 为 NULL，无法进行 DAC 校验 → 缓解：当前系统处于初始化阶段，可接受；对于 resource_id 为 NULL 的私有数据集，仅允许拥有者（通过名称前缀中的 username 匹配）操作
- [风险] query_available_datasets 权限过滤可能影响性能 → 缓解：当前数据集规模小，影响可忽略

## Migration Plan

1. Dataset 表新增 `resource_id` 列（ALTER TABLE ADD COLUMN，可空）
2. 修改 `add_custom_dataset` 将 `resource_id` 写入 Dataset 记录
3. 修改 StateScheduler 中5处缺失 DAC 校验的方法
4. 验证所有操作

## Open Questions

- 无
