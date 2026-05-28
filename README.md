# SDPJ-System

SDPJ-System 是一个大模型安全检测系统，支持多种启动方式，可在Windows、Linux、macOS上运行。

## 快速开始

### 1. Docker一键运行（推荐）

确保已安装Docker和Docker Compose，然后执行：

```bash
docker-compose up -d
```

启动后访问：
- 后端API：http://localhost:8000
- 前端界面：http://localhost:80
- API文档：http://localhost:8000/docs

查看日志：
```bash
docker-compose logs -f
```

停止服务：
```bash
docker-compose down
```

### 2. Linux/macOS启动

确保已安装Python 3.11+和Node.js，然后执行：

```bash
# 添加执行权限
chmod +x start.sh

# 启动系统
./start.sh
```

启动后访问：
- 后端API：https://localhost:8000
- 前端界面：https://localhost:5173
- API文档：https://localhost:8000/docs

### 3. Windows启动

```powershell
.\start.ps1
```

启动后访问：
- 后端API：https://localhost:8000
- 前端界面：https://localhost:5173
- API文档：https://localhost:8000/docs

## 环境要求

- Python 3.11+
- Node.js 16+
- Docker（可选，用于容器化部署）

## 配置说明

复制 `.env.example` 为 `.env` 并根据需要修改配置：

```bash
cp .env.example .env
```

主要配置项：
- `API_HOST`：后端服务监听地址
- `API_PORT`：后端服务端口
- `PYTHON_PATH`：Python解释器路径
- `BACKEND_PORT`：后端服务端口（启动脚本使用）
- `FRONTEND_PORT`：前端服务端口（启动脚本使用）

## 开发指南

### 本地开发

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 安装前端依赖：
```bash
cd sdpj/ui/webui/frontend
npm install
```

3. 启动后端：
```bash
python -m sdpj.ui.webui.backend.app
```

4. 启动前端：
```bash
cd sdpj/ui/webui/frontend
npm run dev
```

### 测试

运行测试：
```bash
pytest tests/
```

## 项目结构

```
SDPJ-System/
├── sdpj/                    # 主应用包
├── tests/                   # 测试目录
├── docker/                  # Docker配置
├── start.ps1                # Windows PowerShell启动脚本
├── start.sh                 # Linux/macOS启动脚本
├── docker-compose.yml       # Docker Compose配置
├── requirements.txt         # Python依赖
└── README.md                # 项目说明
```

## 常见问题

### 端口被占用

如果启动时提示端口被占用，启动脚本会自动尝试清理占用端口的进程。如果清理失败，可以手动终止占用端口的进程：

Windows：
```cmd
netstat -ano | findstr :8000
taskkill /F /PID <进程ID>
```

Linux/macOS：
```bash
lsof -ti :8000 | xargs kill -9
```

### Python版本不兼容

确保使用Python 3.11+版本。可以通过以下命令检查版本：

```bash
python --version
```

### Docker启动失败

确保Docker服务正在运行，并且有足够的磁盘空间和内存。

## 许可证

[待定]
