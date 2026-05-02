# SDPJ-System

基于SDPJ算法的大语言模型安全风险检测系统

## 项目简介

SDPJ-System是一个用于检测大语言模型安全风险的系统,实现了SDPJ(Self-Detection based on Post-Jailbreak)静态和动态自检测算法。

### 核心功能

- **SDPJ静态自检测**: 基于越狱攻击和提示词劫持的静态安全风险检测
- **SDPJ动态自检测**: 基于迭代变异的动态安全风险检测
- **多模态注入检测**: 支持图像、音频、视频等多模态注入攻击检测
- **多编码注入检测**: 支持Base64、URL编码、Unicode等多编码注入检测
- **可视化报告**: 生成详细的检测报告和可视化图表
- **用户管理**: 支持用户注册、登录、权限控制
- **私有配置**: 支持用户自定义检测配置、数据集、模型适配器

### 检测范围

- 提示词注入攻击(直接注入、间接注入)
- 越狱攻击
- 提示词劫持攻击
- 系统提示词泄露攻击

## 技术架构

### 五层架构设计

1. **用户界面层**: CLI命令行 + Web UI(Vue 3 + Element Plus)
2. **应用控制层**: StateScheduler系统状态管理与调度
3. **执行逻辑层**: 检测内核、任务队列、事件日志、用户管理等
4. **抽象驱动层**: 数据处理、LLM接口、用户中心等
5. **基础设施层**: 数据库、LLM适配器、工具库

### 技术栈

**后端:**
- Python 3.11+
- FastAPI 0.115+
- SQLAlchemy 2.0+
- Alembic 1.13+

**前端:**
- Vue 3.4+
- Element Plus 2.8+
- Pinia 2.1+
- ECharts 5.5+

**数据库:**
- SQLite (开发环境)
- PostgreSQL (生产环境)

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- npm 9+

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd SDPJ-System
```

2. 安装Python依赖
```bash
pip install -r requirements.txt
```

3. 初始化数据库
```bash
python -m sdpj.infrastructure.database.sample_db.init_db
python -m sdpj.infrastructure.database.result_db.init_db
python -m sdpj.infrastructure.database.user_db.init_db
```

4. 安装前端依赖
```bash
cd sdpj/ui/webui/frontend
npm install
```

### 运行

**启动后端:**
```bash
python -m sdpj.ui.webui.backend.app
```

**启动前端:**
```bash
cd sdpj/ui/webui/frontend
npm run dev
```

**使用CLI:**
```bash
python -m sdpj --help
```

## Docker部署

```bash
docker-compose up -d
```

## 项目结构

```
SDPJ-System/
├── sdpj/                   # 主应用包
│   ├── ui/                 # 用户界面层
│   ├── control/            # 应用控制层
│   ├── core/               # 执行逻辑层
│   ├── drivers/            # 抽象驱动层
│   └── infrastructure/     # 基础设施层
├── tests/                  # 测试
├── docs/                   # 文档
├── openspec/               # 规格文档
└── docker/                 # Docker配置
```

## 开发指南

### 运行测试

```bash
# 单元测试
pytest tests/unit/

# 集成测试
pytest tests/integration/

# 端到端测试
pytest tests/e2e/
```

### 代码规范

- 遵循PEP 8
- 使用类型注解
- 编写文档字符串

## 许可证

MIT License

## 联系方式

- 项目主页: <repository-url>
- 问题反馈: <issues-url>
