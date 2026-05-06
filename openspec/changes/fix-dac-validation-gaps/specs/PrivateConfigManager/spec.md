## MODIFIED Requirements

### Requirement: add_custom_dataset返回并存储resource_id
`add_custom_dataset` SHALL 将 `resource_id` 写入 Dataset 记录，并在返回值中包含 `resource_id`。

#### Scenario: 导入私有数据集后可查到resource_id
- **WHEN** 调用 `add_custom_dataset` 创建私有数据集
- **THEN** 返回值包含 `dataset_id` 和 `resource_id`，且 Dataset 记录中存储了 `resource_id`
