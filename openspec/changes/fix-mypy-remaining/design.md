## 上下文

SDPJ-System 项目前期已完成一个批次的 mypy 类型错误修复（从150条降至30条），剩余的30条错误分布在9个源文件中。这些错误属于纯类型注解层面，不涉及运行时行为变更。

## 目标 / 非目标

**目标：**
- 修复全部30条 mypy 类型检查错误
- 达到 `mypy sdpj --ignore-missing-imports` 零错误输出

**非目标：**
- 不重构任何业务逻辑
- 不添加新功能
- 不修改测试

## 决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 修复策略 | `cast()` + `type: ignore` + 类型注解修正 | 最小化改动，不改变运行时行为 |
| 接口对齐方式 | 修改接口（Protocol）签名以匹配实现 | 实现已稳定，接口应反映实际需求 |
| 复杂字典 | `type: ignore[dict-item]` / `type: ignore[assignment]` | state_scheduler.py 中动态聚合字典难以静态类型化，保持现有逻辑 |
| 返回类型 | `cast(T, ...)` | 在 ORM 操作返回 Any 处使用 cast 而非重构函数签名 |

## 修复方案按优先级

### 1. 接口签名修复 (blocker)

- **bootstrap.py** (8条)：
  - UtilsLib 需实现 UtilsInterface 全套签名
  - DataProcessor.add_dataset_record 需增加 risk_type 参数以匹配接口
  - LLMServiceInterface 协议需补充

- **report_manager.py** (1条)：
  - export_report 方法中 target_format 参数从 Literal 改为 str

- **reports.py** (2条)：
  - user_id: str→int 转换
  - StateSchedulerInterface 添加 task_id 参数

### 2. 返回类型 cast (minor)

- **task_queue_manager.py**: cast(Task | None, ...)
- **private_config_repo.py**: cast(dict[Any, Any] | None, ...)
- **errors.py**: to_dict 返回类型注解修正

### 3. 复杂字典构建 (major)

- **state_scheduler.py** (15条)：组合 assert + type: ignore 处理

### 4. 其他

- **serialization.py**: type: ignore[import-untyped]
- **builtin_datasets/__init__.py**: None 检查 + 类型注解
- **sdpj_detector/__init__.py**: poc_progress_callback type: ignore

## 风险 / 权衡

- [风险] type: ignore 可能掩盖真正的类型错误 → 缓解措施：仅对明确可论证安全的代码使用，所有 ignore 均标注具体错误码
- [风险] 接口签名修改可能影响其他调用方 → 缓解措施：mypy 全量检查可捕获签名不一致
