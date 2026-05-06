## MODIFIED Requirements

### Requirement: 私有数据集删除的DAC前置校验
StateScheduler 在删除私有数据集前 SHALL 调用 DACManager 的访问权判定，仅允许资源拥有者或被授权用户执行删除。

#### Scenario: 资源拥有者删除自己的私有数据集
- **WHEN** 用户调用 `delete_user_dataset` 且该用户为数据集的拥有者
- **THEN** DAC 校验通过，执行删除操作

#### Scenario: 被授权用户删除他人私有数据集
- **WHEN** 用户调用 `delete_user_dataset` 且该用户在 ACL 中被授权
- **THEN** DAC 校验通过，执行删除操作

#### Scenario: 未授权用户删除他人私有数据集
- **WHEN** 用户调用 `delete_user_dataset` 且该用户既非拥有者也未被授权
- **THEN** 返回错误"无访问权限"，拒绝删除

### Requirement: 私有数据集导出的DAC前置校验
StateScheduler 在导出私有数据集前 SHALL 调用 DACManager 的访问权判定。

#### Scenario: 未授权用户导出他人私有数据集
- **WHEN** 用户调用 `export_dataset_file` 且该用户既非拥有者也未被授权
- **THEN** 返回错误"无访问权限"，拒绝导出

### Requirement: 私有数据集详情查询的DAC前置校验
StateScheduler 在查询私有数据集详情前 SHALL 调用 DACManager 的访问权判定。

#### Scenario: 未授权用户查询他人私有数据集详情
- **WHEN** 用户调用 `query_dataset_detail` 且该用户既非拥有者也未被授权
- **THEN** 返回 None，拒绝查询

### Requirement: 数据集列表按权限过滤
StateScheduler 在查询可用数据集列表时 SHALL 按用户权限过滤：返回所有内置数据集 + 当前用户拥有的私有数据集 + 通过 ACL 被授权访问的私有数据集。

#### Scenario: 普通用户查询数据集列表
- **WHEN** 用户调用 `query_available_datasets`
- **THEN** 返回所有内置数据集 + 该用户拥有的私有数据集 + 该用户被授权访问的私有数据集，不包含其他用户的未授权私有数据集

### Requirement: 检测启动时私有配置的DAC前置校验
StateScheduler 在启动检测时，若请求中包含 `config_id`，SHALL 先调用 DACManager 的访问权判定，校验当前用户是否有权访问该私有配置。

#### Scenario: 未授权用户使用他人私有配置启动检测
- **WHEN** 用户调用 `start_detection` 且 `config_id` 指向他人私有配置，且该用户既非拥有者也未被授权
- **THEN** 返回错误"无访问权限"，拒绝启动检测
