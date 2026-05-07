## ADDED Requirements

### Requirement: 批量检测结果写入接口
DataProcessor SHALL 提供 `append_result_data_batch` 方法，接受结果数据列表，委托 ResultDB 的批量写入能力。

#### Scenario: DataProcessor 批量写入委托
- **WHEN** 调用方通过 DataProcessor 的 `append_result_data_batch` 传入结果数据列表
- **THEN** DataProcessor SHALL 委托 ResultDB 的 `append_result_data_batch` 完成写入

#### Scenario: DataProcessor 批量写入返回结果ID列表
- **WHEN** 批量写入成功完成
- **THEN** DataProcessor SHALL 返回所有新创建条目的结果数据ID列表
