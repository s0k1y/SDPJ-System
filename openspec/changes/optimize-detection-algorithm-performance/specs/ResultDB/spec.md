## ADDED Requirements

### Requirement: 批量检测结果数据写入
ResultDB SHALL 提供 `append_result_data_batch` 方法，在单次数据库 session 中批量写入多条检测结果数据。

#### Scenario: 批量写入多条结果数据
- **WHEN** 调用 `append_result_data_batch` 传入包含多条结果数据的列表
- **THEN** ResultDB SHALL 在单次 session 中使用 `session.add_all` + 单次 `flush` 完成全部写入

#### Scenario: 批量写入前校验报告存在性
- **WHEN** 调用 `append_result_data_batch` 时
- **THEN** ResultDB SHALL 在写入前校验 report_id 存在，若不存在 SHALL 抛出 ValueError

#### Scenario: 批量写入自动生成ID
- **WHEN** 批量写入执行时
- **THEN** 每条结果数据 SHALL 自动生成格式为 `result_{uuid_hex[:16]}` 的唯一ID

#### Scenario: 批量写入返回ID列表
- **WHEN** 批量写入成功完成
- **THEN** ResultDB SHALL 返回所有新创建条目的结果数据ID列表
