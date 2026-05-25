## 为什么

项目中存在30条 mypy 静态类型检查错误，涉及9个源文件。这些错误涵盖接口签名不匹配、返回类型缺失、字典类型推断失败等问题。修复它们可以保证代码类型安全性，避免运行时类型错误，并使项目达到零 mypy 错误的目标。

## 发生了什么变化

- 修复 errors.py 中 to_dict() 返回类型注解（由 dict[str,str] 改为 dict[str,Any]）
- 修复 serialization.py 中 PyYAML stub 缺失导致的 import-untyped 警告
- 修复 report_manager.py 中 export_report 方法签名与接口不一致（Literal → str）
- 修复 builtin_datasets/__init__.py 中列表推导式类型不兼容及 None 不可迭代问题
- 修复 task_queue_manager.py 中返回 Any 而非 Task|None 的问题
- 修复 sdpj_detector/__init__.py 中 poc_progress_callback 类型不兼容
- 修复 state_scheduler.py 中多处 task_group_id 为 Any|None 需 str 以及复杂字典构建类型不匹配
- 修复 private_config_repo.py 中返回 Any 而非 dict|None 的问题
- 修复 bootstrap.py 中多接口不兼容（UtilsLib/DataProcessor vs Interface）
- 修复 reports.py 中 request.state.user_id 类型赋值错误和 export_report 参数不匹配

## 能力

### 新增能力

无需新增业务能力，此变更为纯类型修正。

### 修改的能力

类型注解修正，不影响任何现有业务能力。

## 影响

- 受影响文件：errors.py, serialization.py, report_manager.py, builtin_datasets/__init__.py, task_queue_manager.py, sdpj_detector/__init__.py, state_scheduler.py, private_config_repo.py, bootstrap.py, reports.py, state_scheduler_interface.py, data_processor_interface.py
- 影响面：仅类型注解层面，无运行时行为变更
- 依赖项：无新增依赖
