# SDPJ CLI 使用手册

## 启动方式

```bash
cd SDPJ-System
conda activate SDPJ-System
sdpj [命令]
```

`--version` 查看版本号。

`--help` 查看帮助。

***

## 用户账号与权限管理 `User`

### `register` — 注册

```
sdpj User register --username 用户名 [--password 密码]
```

### `login` — 登录

```
sdpj User login --username 用户名 [--password 密码]
```

### `logout` — 登出

```
sdpj User logout
```

### `switch` — 切换账号

```
sdpj User switch --username 用户名 [--password 密码]
```

### `profile` — 查看当前用户资料

```
sdpj User profile
```

### `password` — 修改密码

```
sdpj User password --old 旧密码 --new 新密码
```

### `unregister` — 注销当前账号

```
sdpj User unregister
```

### `resources` — 列出拥有的受控资源

```
sdpj User resources
```

### `auth` — 访问授权管理

#### `grant` — 授权其他用户访问私有资源

```
sdpj User auth grant --resource-id 资源ID --target-username 目标用户名
```

#### `revoke` — 撤销授权

```
sdpj User auth revoke --acl-id 访问控制项ID
```

#### `show` — 查看某资源的授权清单

```
sdpj User auth show --resource-id 资源ID
```

#### `check` — 检查当前用户对某资源的访问权限

```
sdpj User auth check --resource-id 资源ID
```

### `list` — 列出所有用户（管理员）

```
sdpj User list
```

列出当前实例上已注册的全部用户。无需登录即可执行。

> **管理员说明**：CLI 默认部署在本地终端，SQLite 数据库文件直接存放在本机磁盘上，终端操作者天然拥有对数据库的完全读写权限，因此**部署 CLI 的人就是管理员**。系统不在数据库层面维护 `role` 字段——能执行 CLI 命令即为管理资格。同理，`System` 组的运维命令（`logs`、`watch` 等）也不做登录校验。

### `delete-user` — 删除用户（管理员）

```
sdpj User delete-user --user-id 用户ID
```

删除指定 ID 的用户账号及其关联的私有资源、授权记录。操作不可逆，执行前会有确认提示。

> 管理逻辑同上：本地 CLI 操作者即管理员，无需额外鉴权。

***

## 私有检测配置与资源管理 `Config`

> 私有检测配置与私有大模型适配器本质上是同一功能——配置是蓝图（持久化存储），适配器是运行时实例。创建配置时自动注册适配器，删除配置时自动注销适配器，系统启动时也会从已有配置中恢复所有适配器。

### `create` — 创建配置并自动注册适配器

```
sdpj Config create --model <模型标识> --request-format <请求格式> --api-key <API密钥> --base-url <API地址> --timeout <超时秒数> --max-rps <每秒最大请求数> --max-concurrency <最大并发数>
```

| 参数                  | 说明                            |
| ------------------- | ----------------------------- |
| `--model`           | 模型标识                          |
| `--request-format`  | 请求格式(openai/anthropic/custom) |
| `--api-key`         | API 密钥                        |
| `--base-url`        | API 地址                        |
| `--timeout`         | 请求超时秒数                        |
| `--max-rps`         | 每秒最大请求数                       |
| `--max-concurrency` | 最大并发数                         |

所有参数均为必填。从文件创建请使用 `import`。

### `list` — 列出配置

```
sdpj Config list
```

### `view` — 查看配置

```
sdpj Config view --config-id 配置ID
```

### `update` — 更新配置（热重载适配器）

```
sdpj Config update --config-id <配置ID> --model <模型标识> --request-format <请求格式> --api-key <API密钥> --base-url <API地址> --timeout <超时秒数> --max-rps <每秒最大请求数> --max-concurrency <最大并发数>
```

| 参数                  | 说明                            |
| ------------------- | ----------------------------- |
| `--config-id`       | 配置ID                          |
| `--model`           | 模型标识                          |
| `--request-format`  | 请求格式(openai/anthropic/custom) |
| `--api-key`         | API 密钥                        |
| `--base-url`        | API 地址                        |
| `--timeout`         | 请求超时秒数                        |
| `--max-rps`         | 每秒最大请求数                       |
| `--max-concurrency` | 最大并发数                         |

所有参数均为必填。

### `import` — 导入配置并自动注册适配器

```
sdpj Config import <配置文件绝对路径>
```

### `delete` — 删除配置并自动注销适配器

```
sdpj Config delete --config-id 配置ID
```

### `export` — 导出配置

```
sdpj Config export --config-id 配置ID [--format json|yaml] [--output 路径]
```

### `verify` — 测试配置可用性

```
sdpj Config verify --config-id 配置ID
```

向模型 API 发送健康检查请求，验证配置中的连接、认证、响应格式是否正常。

### `upload-dataset` — 上传私有数据集

```
sdpj Config upload-dataset <数据集文件绝对路径>
```

数据集名称从文件名自动截取。

### `remove-dataset` — 移除私有数据集

```
sdpj Config remove-dataset --dataset-id 数据集ID [--resource-id 资源ID]
```

### `export-dataset` — 导出数据集

```
sdpj Config export-dataset --id 数据集ID [--output 输出文件路径]
```

| 参数         | 说明                    |
| ---------- | --------------------- |
| `--id`     | 数据集ID **\[必填]**       |
| `--output` | 输出文件路径，不指定则保存到当前目录    |

### `dataset list` — 列出可用数据集

```
sdpj Config dataset list
```

### `dataset detail` — 查看数据集详情

```
sdpj Config dataset detail --id 数据集ID
```

***

## 检测 `Detect`

### `task start` — 启动检测任务

```
sdpj Detect task start --model-id 模型标识 [选项]
```

| 选项                            | 说明                                                                                                                |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `--model-id TEXT`             | 被测大模型标识（支持模型名如 `deepseek-v4-pro` 或数字型配置ID）**\[必填]**                                                               |
| `--dataset INTEGER`           | 检测数据集ID，可多选：`--dataset 1 --dataset 2`                                                                             |
| `--type static\|dynamic`      | 检测类型，默认 `static`                                                                                                  |
| `--force-refresh`             | 强制重建PoC池缓存                                                                                                        |
| `--jailbreak-dataset INTEGER` | 指定越狱数据集ID，可多选（仅 `--force-refresh` 时有效），不指定时自动使用内置默认数据集 (`jailbreak_llm`, `augmented_jailbreak`, `jailbreakv_28k`) |
| `--config-id INTEGER`         | 私有检测配置ID                                                                                                          |
| `--max-iter INTEGER`          | 动态算法最大迭代次数，默认 3                                                                                                   |

示例：

```
# 对 deepseek 用数据集 1 和 2 做静态检测
sdpj Detect task start --model-id deepseek-v4-pro --dataset 1 --dataset 2

# 强制重建PoC池 + 指定越狱数据集
sdpj Detect task start --model-id deepseek-v4-pro --dataset 1 --force-refresh --jailbreak-dataset 5 --jailbreak-dataset 6

# 动态检测
sdpj Detect task start --model-id deepseek-v4-pro --dataset 1 --type dynamic
```

### `task progress` — 查询进度

```
sdpj Detect task progress                  # 全部任务组视图
sdpj Detect task progress --task-id TASK_ID  # 单个子任务
```

### `task run` — 并发执行队列任务

```
sdpj Detect task run [--concurrency 并发数]
```

### `task trace` — 实时追踪 LLM 请求/响应

```
sdpj Detect task trace [--show-full]
```

`--show-full` 显示完整内容，默认截断长文本。按 Ctrl+C 退出。

### `task cancel` — 取消任务

```
sdpj Detect task cancel --task-id TASK_ID     # 取消子任务
sdpj Detect task cancel --group-id GROUP_ID   # 取消整个任务组
```

***

## 报告 `Report`

### `generate` — 生成检测报告

```
sdpj Report generate --group-id 任务组ID [--type static|dynamic]
```

### `view` — 查看报告

```
sdpj Report view --group-id 任务组ID
```

### `list` — 报告列表

```
sdpj Report list [--model-id 模型ID]
```

### `export` — 导出报告

```
sdpj Report export --group-id 任务组ID [选项]
```

| 选项                           | 说明                 |
| ---------------------------- | ------------------ |
| `--format json\|yaml\|jsonl` | 导出格式，默认 `json`     |
| `--task-id TEXT`             | 子任务ID（导出单任务级别报告）   |
| `--output TEXT`              | 输出文件路径，不指定则保存到当前目录 |

示例：

```
sdpj Report export --group-id tg-001
sdpj Report export --group-id tg-001 --format yaml --task-id task-001
sdpj Report export --group-id tg-001 --output ./my_report.json
```

### `delete` — 删除报告

```
sdpj Report delete --target-id 目标ID [--granularity task_group|task|report|result_data]
```

### `statistics` — 合规统计

```
sdpj Report statistics
```

### `visualization` — 任务组可视化数据

```
sdpj Report visualization --group-id 任务组ID
```

### `task-visualization` — 单任务可视化数据

```
sdpj Report task-visualization --task-id 任务ID
```

***

## 系统管理 `System`

### `status` — 查询系统状态

```
sdpj System status
```

### `logs` — 查询系统日志

```
sdpj System logs [--category operation|runtime|error]
                 [--module 来源模块]
                 [--user-id 用户ID]
                 [--page 页码]
                 [--page-size 每页条数]
```

### `watch` — 实时监听系统状态变更

```
sdpj System watch [--interval 轮询秒数]
```

按 Ctrl+C 退出，再次按 Ctrl+C 强制退出。

### `watch-errors` — 实时监听系统异常

```
sdpj System watch-errors
```

按 Ctrl+C 退出，再次按 Ctrl+C 强制退出。

***

## 典型工作流

```bash
# 1. 注册并登录
sdpj User register --username alice --password mypass
sdpj User login --username alice --password mypass

# 2. 查看可用数据集
sdpj Config dataset list

# 3. 启动检测
sdpj Detect task start --model-id deepseek-v4-pro --dataset 1 --dataset 2

# 4. 查看进度
sdpj Detect task progress

# 5. 执行任务
sdpj Detect task run

# 6. 生成报告
sdpj Report generate --group-id <任务组ID>

# 7. 导出报告
sdpj Report export --group-id <任务组ID> --output report.json
```

