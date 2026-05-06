## Why

规格文档 StateScheduler.md 职责16明确要求：在使用私有资源前的访问权前置校验。但当前代码中，私有数据集的删除/导出/详情查询、检测启动时读取私有配置、数据集列表查询等操作均缺失 DAC 校验，任何已登录用户只要知道 ID 就能访问/操作他人的私有资源。

根本原因：Dataset 表（SampleDB）和 Resource 表（UserDB）之间没有映射关系。`add_custom_dataset` 注册了 Resource 但丢弃了 `resource_id`，导致后续操作无法通过 `resource_id` 进行 DAC 校验。

## What Changes

- 在 SampleDB 的 Dataset 表中新增 `resource_id` 列（可空，内置数据集为 NULL），建立 dataset→resource 的映射
- 修改 `add_custom_dataset` 将 `resource_id` 写入 Dataset 记录
- 修改 `delete_user_dataset` 查找 `resource_id` 并校验 DAC 访问权
- 修改 `export_dataset_file` 对私有数据集校验 DAC 访问权
- 修改 `query_dataset_detail` 对私有数据集校验 DAC 访问权
- 修改 `query_available_datasets` 按用户权限过滤数据集列表
- 修改 `start_detection` 在读取私有配置前校验 DAC 访问权

## Capabilities

### Modified Capabilities
- `StateScheduler`: 补齐职责16中缺失的 DAC 前置校验，覆盖私有数据集删除/导出/详情查询、私有配置读取、数据集列表权限过滤
- `SampleDB`: Dataset 表新增 `resource_id` 列，建立与 UserDB Resource 表的映射关系
- `PrivateConfigManager`: `add_custom_dataset` 返回值包含 `resource_id`，并将 `resource_id` 写入 Dataset 记录

## Impact

- **数据库**: SampleDB 的 Dataset 表需新增 `resource_id` 列（可空整数，内置数据集为 NULL）
- **后端**: `state_scheduler.py`（5处DAC校验补齐）、`private_config_manager.py`（add_custom_dataset 修改）、`data_processor.py`（add_dataset_record 传递 resource_id）、`sample_db.py`（create_dataset 传递 resource_id）、`dataset_repo.py`（create 方法写入 resource_id）、`models.py`（Dataset 模型新增 resource_id 字段）
- **前端**: 无需修改，错误提示由后端统一返回
