## 1. SystemMeta 模型与数据库支持

- [ ] 1.1 在 `sdpj/infrastructure/database/sample_db/models.py` 中新增 `SystemMeta` ORM 模型（key TEXT PRIMARY KEY, value TEXT）
- [ ] 1.2 在 `sdpj/infrastructure/database/sample_db/sample_db.py` 中新增 `get_system_meta(key)` 和 `set_system_meta(key, value)` 方法
- [ ] 1.3 验证 `create_tables()` 自动创建 `system_meta` 表

## 2. 原生 SQL 批量插入

- [ ] 2.1 在 `sdpj/infrastructure/database/sample_db/sample_db.py` 中新增 `bulk_insert_samples(records, batch_size=5000)` 方法，使用 SQLAlchemy Core `insert()` 语句
- [ ] 2.2 将 `load_builtin_datasets` 中的 `bulk_add_samples` 调用替换为 `bulk_insert_samples`
- [ ] 2.3 验证原生 SQL 插入结果与 ORM 插入结果一致

## 3. manifest.json 预计算清单

- [ ] 3.1 编写脚本生成 `sdpj/infrastructure/database/sample_db/builtin_datasets/manifest.json`，包含每个 jsonl 文件的相对路径、行数和 MD5
- [ ] 3.2 运行脚本生成 manifest.json 文件

## 4. 重写 load_builtin_datasets

- [ ] 4.1 合并两次文件读取为单次遍历（边读边解析边计数）
- [ ] 4.2 使用 `asyncio.to_thread()` 包装文件读取操作
- [ ] 4.3 集成 manifest.json 读取：manifest 存在且 MD5 匹配时使用预计算行数，否则回退逐行计数
- [ ] 4.4 集成 system_meta 检查：`builtin_datasets_loaded=True` 时直接返回，`force_reload=True` 时强制重新加载
- [ ] 4.5 加载成功后写入 `system_meta` 中 `builtin_datasets_loaded=True`

## 5. 调整 bootstrap.py

- [ ] 5.1 修改 `_init_db()` 中的 `load_builtin_datasets` 调用，传递 `force_reload=False`
- [ ] 5.2 确保 seed_data.py 的调用也兼容新的 `load_builtin_datasets` 签名

## 6. 端到端验证

- [ ] 6.1 删除现有 sdpj.db，运行 seed_data.py 验证首次加载正确性
- [ ] 6.2 启动 FastAPI 后端，验证二次启动跳过加载（检查日志无文件读取）
- [ ] 6.3 验证 `force_reload=True` 时强制重新加载
- [ ] 6.4 验证 manifest.json 不存在时回退到逐行计数
