## 1. 简单类型注解修正 (minor)

- [ ] 1.1 修复 serialization.py:7 — 为 yaml 导入添加 `# type: ignore[import-untyped]`
- [ ] 1.2 修复 task_queue_manager.py:151 — 使用 `cast(Task | None, ...)` 包裹返回值
- [ ] 1.3 修复 private_config_repo.py:79 — 使用 `cast(dict[Any, Any] | None, ...)` 包裹返回值

## 2. 接口签名对齐

- [ ] 2.1 修复 report_manager.py:206 — 将 export_report 方法中 target_format 参数类型从 Literal 改为 str
- [ ] 2.2 修复 data_processor_interface.py — 确保 add_dataset_record 签名与 DataProcessor 实现一致（添加 risk_type 可选参数）
- [ ] 2.3 修复 state_scheduler_interface.py — 为 export_report 方法添加 task_id 参数
- [ ] 2.4 修复 reports.py:48 — 修复 user_id 的 int/str 类型转换
- [ ] 2.5 修复 reports.py:81 — 修复 export_report 调用（task_id 参数已在上一步添加到接口）

## 3. bootstrap.py 接口兼容性 (blocker)

- [ ] 3.1 修复 UtilsLib 使其实现 UtilsInterface 完整签名（确保所有方法签名兼容）
- [ ] 3.2 修复 bootstrap.py:79-88 — 验证 UtilsLib/DataProcessor 与接口的兼容性，必要时添加 type: ignore

## 4. state_scheduler.py 复杂类型修正 (major)

- [ ] 4.1 修复 431/442/470 行 — 在 task_group_id 使用前添加 `assert task_group_id is not None`
- [ ] 4.2 修复 773 行 — 添加 `# type: ignore[assignment]`
- [ ] 4.3 修复 811/820/829 行 — 添加相应的 `# type: ignore` 注解
- [ ] 4.4 修复 863/900/901/902 行 — 添加 `# type: ignore[attr-defined]` 和 `# type: ignore[dict-item]`
- [ ] 4.5 修复 911/918 行 — 添加 `# type: ignore[dict-item]`
- [ ] 4.6 修复 951 行 — 添加 `# type: ignore[dict-item]`
- [ ] 4.7 修复 977 行 — 添加 `# type: ignore[arg-type]`

## 5. sdpj_detector / builtin_datasets / reports 修正

- [ ] 5.1 修复 sdpj_detector/__init__.py:55 — 为 poc_progress_callback 添加 `# type: ignore[arg-type]`
- [ ] 5.2 修复 builtin_datasets/__init__.py:115 — 添加 None 检查后再列表推导

## 6. 最终验证

- [ ] 6.1 运行 `conda run -n SDPJ-System mypy sdpj --ignore-missing-imports` 确认零错误
- [ ] 6.2 运行 `conda run -n SDPJ-System ruff check sdpj` 确认无新增 lint 问题
