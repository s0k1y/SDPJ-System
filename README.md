# SDPJ-System

SDPJ-System 是一个大模型安全检测系统，支持 WebUI 和 CLI 两种使用方式。


## 一键安装

### Windows (PowerShell)

```powershell
.\install.ps1
```

### Linux / macOS

```bash
chmod +x install.sh && ./install.sh
```

### Docker

```bash
docker-compose up -d
```

---

## 一键启动

安装完成后，使用以下命令启动：

### 启动 WebUI（图形界面）

**Windows:**
```powershell
.\start.ps1
```

**Linux / macOS:**
```bash
./start.sh
```

**Docker:**
```bash
# Docker 方式安装后已自动启动，无需额外操作
# 如已停止，重新启动：
docker-compose up -d
```

启动后访问：
- 前端界面：https://localhost:5173 (Docker 方式为 http://localhost:80)
- 后端API：https://localhost:8000
- API文档：https://localhost:8000/docs

### 启动 CLI（命令行）

```bash
sdpj -h
```

---

## 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 必须 |
| Node.js | 16+ | 仅 WebUI 需要，安装脚本会自动检测 |
| Docker | 最新版 | 仅 Docker 方式需要 |

---

## 常见问题

### 安装失败

1. **Python 版本过低**：安装 Python 3.11+ 或使用 conda：
   ```bash
   conda create -n SDPJ-System python=3.11
   conda activate SDPJ-System
   ```

2. **npm install 失败**：清除缓存后重试：
   ```bash
   cd sdpj/ui/webui/frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

### 启动失败

1. **端口被占用**：启动脚本会自动清理，如仍有问题手动清理：
   - Windows: `netstat -ano | findstr :8000` 然后 `taskkill /F /PID <进程ID>`
   - Linux/macOS: `lsof -ti :8000 | xargs kill -9`

2. **Docker 启动失败**：确保 Docker 服务正在运行

---

## 许可证

Copyright (c) 2026 SDPJ-System. All rights reserved.
