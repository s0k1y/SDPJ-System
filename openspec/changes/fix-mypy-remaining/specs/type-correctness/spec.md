## 新增需求

### 需求: mypy 静态类型检查零错误
系统 SHALL 通过 `mypy sdpj --ignore-missing-imports` 命令的零错误检查。

#### 场景: 执行 mypy 检查无错误
- **当** 执行 `conda run -n SDPJ-System mypy sdpj --ignore-missing-imports` 时
- **则** 命令退出码为0，输出无任何 error 级别的问题

### 需求: 接口与实现签名一致
所有 Interface (Protocol) 类的方法签名 SHALL 与其对应的实现类方法签名兼容。

#### 场景: bootstrap.py 中依赖注入类型兼容
- **当** bootstrap.py 中将具体实现类实例注入到期望接口类型的参数时
- **则** mypy 不报告 arg-type 错误

### 需求: 函数返回类型明确
所有函数 SHALL 具有与实际返回值兼容的返回类型注解，不得返回 Any 类型而不通过 cast 明确表达。

#### 场景: ORM 操作返回类型通过 cast 明确
- **当** 函数返回 SQLAlchemy ORM 查询结果时
- **则** 使用 `cast()` 将返回值转换为声明类型
