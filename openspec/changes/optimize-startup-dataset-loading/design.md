## Context

当前 `load_builtin_datasets()` 在 FastAPI lifespan 中被调用，加载 17 个 jsonl 文件（共约 86MB/13 万条）。存在三个性能缺陷：

1. 每个文件被读取两次：第一次逐行计数，第二次逐行解析 JSON
2. 同步 `open()` + `readline()` 阻塞 asyncio 事件循环
3. 使用 ORM `session.add_all()` 批量插入，每条记录创建一个 Python 对象

此外，`start.ps1` 的 seed_data 和 FastAPI lifespan 重复加载同一批数据集；二次启动时幂等检查仍需逐文件计数。

## Goals / Non-Goals

**Goals:**

- 将每个文件的两次读取合并为单次遍历
- 文件 I/O 不阻塞 asyncio 事件循环
- 批量插入使用原生 SQL 绕过 ORM 层
- 二次启动时通过 `system_meta` 表直接跳过加载，零文件读取
- 通过 `manifest.json` 预计算清单替代运行时逐行计数

**Non-Goals:**

- 不将数据集加载从 FastAPI lifespan 中剥离（思路一不做）
- 不修改前端代码
- 不修改 `start.ps1` 脚本逻辑

## Decisions

### D1: 单次遍历读取

**选择**：将计数和解析合并到一次文件遍历中，边读边解析边计数。

**替代方案**：维持两次读取但用 `wc -l` 计数 — 跨平台兼容性差，且无法区分空行。

**理由**：单次遍历直接减少 50% 文件 I/O，实现简单，无副作用。

### D2: 异步文件 I/O

**选择**：使用 `asyncio.to_thread()` 将同步文件读取推到线程池。

**替代方案**：使用 `aiofiles` — 需引入新依赖，且其底层也是线程池封装。

**理由**：`asyncio.to_thread()` 是标准库方案，零依赖，效果等价。

### D3: 原生 SQL 批量插入

**选择**：使用 `session.execute(insert(DetectionSample), batch_data)` 替代 `session.add_all(orm_objects)`。

**替代方案**：使用 `conn.execute(text("INSERT INTO ..."), batch_data)` — 绕过 SQLAlchemy Core，失去类型安全。

**理由**：SQLAlchemy Core 的 `insert()` 语句绕过 ORM 的实例化和属性追踪，性能提升 5-10 倍，同时保留表名/列名的编译期安全。

### D4: system_meta 表

**选择**：新增 `system_meta` 表（key TEXT PRIMARY KEY, value TEXT），记录 `builtin_datasets_loaded = True`。

**替代方案**：用文件标记（如 `.last_log_cleanup` 的做法）— 文件标记与数据库状态可能不一致。

**理由**：数据库内标记保证事务一致性，查询成本极低（1 条 SELECT），且与现有架构一致。

### D5: manifest.json 预计算清单

**选择**：在 `builtin_datasets/` 目录下生成 `manifest.json`，存储每个 jsonl 文件的相对路径、行数和 MD5。

**替代方案**：运行时动态计算 — 正是要消除的性能瓶颈。

**理由**：数据集文件是只读的版本控制资源，行数和 MD5 在构建时确定，运行时计算纯属浪费。manifest 文件约 1KB，读取成本可忽略。

## Risks / Trade-offs

- **[manifest 与文件不同步]** → 如果开发者新增/修改了 jsonl 文件但未更新 manifest，加载器会检测到不匹配并回退到逐行计数模式（安全降级）
- **[system_meta 与实际数据不一致]** → 如果数据库被手动修改但标记未更新，提供 `force_reload` 参数强制重新加载
- **[原生 SQL 插入绕过 ORM 事件]** → 当前 DetectionSample 模型无 ORM 事件钩子，无影响；若未来添加需同步调整
