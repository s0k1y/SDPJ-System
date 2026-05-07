## Why

系统启动时 `load_builtin_datasets()` 加载约 86MB/13 万条内置数据集，存在三个性能缺陷：每个文件被读取两次（计数+解析）、同步 I/O 阻塞 asyncio 事件循环、ORM 批量插入性能差。此外，`start.ps1` 的 seed_data 和 FastAPI lifespan 重复加载同一批数据集，二次启动仍需逐文件计数做幂等检查。启动时间在分钟级，严重影响开发体验。

## What Changes

- 合并 `load_builtin_datasets` 中每个文件的两次读取为单次遍历（边读边解析边计数）
- 将同步文件 I/O 改为 `asyncio.to_thread()` 避免阻塞事件循环
- 将 ORM 批量插入（`session.add_all`）替换为原生 SQL `insert()` 批量插入
- 新增 `system_meta` 表记录内置数据集加载状态，二次启动时直接跳过加载（连文件都不读）
- 新增 `manifest.json` 预计算清单文件，存储每个 jsonl 文件的行数和 MD5，替代运行时逐行计数

## Capabilities

### New Capabilities

- `dataset-loading-optimization`: 内置数据集加载性能优化，涵盖单次遍历读取、异步 I/O、原生 SQL 插入、system_meta 状态标记、manifest 预计算清单

### Modified Capabilities

- `SampleDB`: 新增 `system_meta` 表的创建与查询能力，新增原生 SQL 批量插入方法

## Impact

- `sdpj/infrastructure/database/sample_db/builtin_datasets/__init__.py` — 核心重写
- `sdpj/infrastructure/database/sample_db/sample_db.py` — 新增 `bulk_insert_samples` 原生 SQL 方法，新增 `system_meta` 相关方法
- `sdpj/infrastructure/database/sample_db/models.py` — 新增 `SystemMeta` ORM 模型
- `sdpj/infrastructure/database/sample_db/session.py` — `create_tables` 自动包含新模型
- `sdpj/infrastructure/database/sample_db/builtin_datasets/manifest.json` — 新增预计算清单
- `sdpj/bootstrap.py` — `_init_db` 调整为检查 system_meta 后条件加载
