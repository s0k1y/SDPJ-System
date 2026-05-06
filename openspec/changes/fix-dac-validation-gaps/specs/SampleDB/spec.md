## MODIFIED Requirements

### Requirement: Dataset表新增resource_id列
Dataset 表 SHALL 新增 `resource_id` 列（可空整数），用于建立与 UserDB Resource 表的映射关系。内置数据集的 `resource_id` 为 NULL，私有数据集的 `resource_id` 指向 UserDB 中对应的 Resource 记录。

#### Scenario: 创建私有数据集时写入resource_id
- **WHEN** 系统创建私有数据集
- **THEN** Dataset 记录的 `resource_id` 字段写入对应的 Resource 记录 ID

#### Scenario: 内置数据集的resource_id为NULL
- **WHEN** 系统查询内置数据集
- **THEN** Dataset 记录的 `resource_id` 为 NULL
