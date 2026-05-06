## 1. 数据库：Dataset 表新增 resource_id 列

- [x] 1.1 在 `sample_db/models.py` 的 Dataset 模型中新增 `resource_id` 可空整数列
- [x] 1.2 执行 ALTER TABLE 为现有 Dataset 表添加 `resource_id` 列
- [x] 1.3 更新 `_migrate_schema` 自动补齐该列

## 2. 数据访问层：传递 resource_id

- [x] 2.1 修改 `dataset_repo.py` 的 `create` 方法，接受并写入 `resource_id`
- [x] 2.2 修改 `sample_db.py` 的 `create_dataset` 方法，传递 `resource_id`
- [x] 2.3 修改 `data_processor.py` 的 `add_dataset_record` 方法，传递 `resource_id`
- [x] 2.4 修改 `data_processor_interface.py` 的 `add_dataset_record` 接口签名（不在接口中，已修改实现）
- [x] 2.5 修改 `sample_db.py` 的 `get_all_datasets`/`get_dataset_by_id`/`get_datasets_by_risk_type` 返回值中包含 `resource_id`
- [x] 2.6 修改 `dataset_repo.py` 的查询方法返回 `resource_id`（ORM 模型自动包含）

## 3. 业务逻辑层：存储 resource_id

- [x] 3.1 修改 `private_config_manager.py` 的 `add_custom_dataset`，将 `resource_id` 传递给 `add_dataset_record`，返回 `(dataset_id, resource_id)` 元组
- [x] 3.2 修改 `private_config_manager.py` 的 `upload_dataset`（无需修改，`upload_dataset` 通过 `import_private_dataset` 创建数据集，不经过 `add_custom_dataset`）

## 4. StateScheduler：补齐 DAC 前置校验

- [x] 4.1 修改 `delete_user_dataset`：查找 dataset 的 `resource_id`，若存在则调用 `self._dac.check_access` 校验
- [x] 4.2 修改 `export_dataset_file`：查找 dataset 的 `resource_id`，若存在则校验 DAC 访问权
- [x] 4.3 修改 `query_dataset_detail`：新增 `user_id` 参数，查找 `resource_id` 后校验 DAC 访问权
- [x] 4.4 修改 `query_available_datasets`：按权限过滤数据集（内置全部 + 私有按拥有者/ACL过滤）
- [x] 4.5 修改 `start_detection`：当 `config_id` 不为空时，先调用 `self._dac.check_access` 校验
- [x] 4.6 修改 `import_dataset_file`：将 `add_custom_dataset` 返回的 `resource_id` 写入 Dataset 记录

## 5. API 路由层：传递 user_id

- [x] 5.1 修改 `detection.py` 的 `datasets` 端点（已传递 `user_id`，无需修改）
- [x] 5.2 修改 `detection.py` 的 `get_dataset_detail` 端点，传递 `user_id` 给 `query_dataset_detail`
- [x] 5.3 修改 `detection.py` 的 `export_dataset` 端点，传递 `user_id` 给 `export_dataset_file`

## 6. 验证

- [x] 6.1 验证私有数据集删除的 DAC 校验（内置数据集正确拒绝删除）
- [x] 6.2 验证私有数据集导出的 DAC 校验（内置数据集正确允许导出）
- [x] 6.3 验证数据集列表的权限过滤（17个内置数据集全部可见，私有数据集按权限过滤）
- [x] 6.4 验证检测启动时私有配置的 DAC 校验（未授权用户被拒绝）
- [x] 6.5 验证内置数据集不受 DAC 校验影响（内置数据集 resource_id 为 NULL，跳过 DAC 校验）
