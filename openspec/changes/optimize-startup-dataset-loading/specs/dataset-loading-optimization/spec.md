## ADDED Requirements

### Requirement: 单次遍历读取数据集文件
`load_builtin_datasets()` 对每个 jsonl 文件 SHALL 只执行一次文件读取，在同一次遍历中完成行计数和 JSON 解析。

#### Scenario: 加载单个 jsonl 文件
- **WHEN** `load_builtin_datasets()` 处理一个 jsonl 文件
- **THEN** 该文件仅被打开和读取一次，同时产出 `file_line_count` 和 `records` 列表

### Requirement: 异步文件 I/O
`load_builtin_datasets()` 中的文件读取操作 SHALL 通过 `asyncio.to_thread()` 在线程池中执行，不得阻塞 asyncio 事件循环。

#### Scenario: 大文件读取不阻塞事件循环
- **WHEN** 加载 60MB 的 jsonl 文件时
- **THEN** asyncio 事件循环不被阻塞，其他协程可正常调度

### Requirement: 原生 SQL 批量插入
`SampleDB.bulk_add_samples()` SHALL 使用 SQLAlchemy Core `insert()` 语句执行批量插入，绕过 ORM 实例化。

#### Scenario: 批量插入 5000 条记录
- **WHEN** 调用 `bulk_add_samples()` 插入 5000 条记录
- **THEN** 使用 `session.execute(insert(DetectionSample), batch_data)` 而非 `session.add_all(orm_objects)`

#### Scenario: 批量插入结果正确性
- **WHEN** 使用原生 SQL 批量插入后查询数据库
- **THEN** 插入的记录与原始数据完全一致（subtype、poc、dataset_id 字段正确）

### Requirement: system_meta 表状态标记
系统 SHALL 在 `sample_db` 中维护 `system_meta` 表（key TEXT PRIMARY KEY, value TEXT），用于记录内置数据集加载状态。

#### Scenario: 首次加载数据集
- **WHEN** `load_builtin_datasets()` 成功完成所有数据集加载
- **THEN** `system_meta` 表中写入 `builtin_datasets_loaded = True`

#### Scenario: 二次启动跳过加载
- **WHEN** `load_builtin_datasets()` 被调用且 `system_meta` 中 `builtin_datasets_loaded = True`
- **THEN** 直接返回，不读取任何 jsonl 文件

#### Scenario: 强制重新加载
- **WHEN** `load_builtin_datasets(force_reload=True)` 被调用
- **THEN** 忽略 `builtin_datasets_loaded` 标记，重新执行完整加载流程

### Requirement: manifest.json 预计算清单
`builtin_datasets/` 目录下 SHALL 存在 `manifest.json` 文件，预记录每个 jsonl 文件的相对路径、行数和 MD5 校验值。

#### Scenario: manifest 存在且匹配
- **WHEN** `manifest.json` 存在且某文件的 MD5 与 manifest 记录一致
- **THEN** 直接使用 manifest 中的行数，不逐行计数

#### Scenario: manifest 不存在或文件不匹配
- **WHEN** `manifest.json` 不存在，或某文件的 MD5 与 manifest 记录不一致
- **THEN** 回退到逐行计数模式，确保数据正确性

## MODIFIED Requirements

### Requirement: SampleDB 数据库表创建
`SampleDB` 的 `create_tables()` SHALL 同时创建 `system_meta` 表，包含 `key`（TEXT PRIMARY KEY）和 `value`（TEXT）两列。

#### Scenario: 首次创建表
- **WHEN** 调用 `sample_sm.create_tables()`
- **THEN** 除原有表外，`system_meta` 表也被创建
