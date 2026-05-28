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
本系统及相关文档文件（"系统"）的著作权归版权所有者所有。版权所有者保留所有未在此明确授予的权利。

允许行为（无需另行授权）：
为完成与本系统相关的毕业设计评审之目的，尊敬的评审老师、尊敬的答辩委员会成员可以：
- 下载一份本系统的副本至本地计算机；
- 运行本系统以验证其功能与结果；
- 在评审报告中引用本系统的代码片段。

其他任何人不得以任何方式使用、复制或分发本系统,包括但不限于:
- 禁止将本系统或其任何部分用于商业目的；
- 复制、修改、合并、发布、分发、再许可、销售本系统的副本；
- 将本系统作为服务对外提供。



The copyright of this system and associated documentation files (the "System") belongs
to the copyright owner. The copyright owner retains all rights not expressly granted herein.

Permitted Acts (without separate authorization):
For the purpose of completing the graduation design review related to this System,
esteemed review instructors and esteemed defense committee members may:
- Download one copy of the System to a local computer;
- Run the System to verify its functionality and results;
- Quote brief code snippets from the System in review reports.

No other person may use, copy, or distribute the System in any manner, including but not limited to:
- Using the System or any part thereof for commercial purposes is prohibited;
- Copy, modify, merge, publish, distribute, sublicense, or sell copies of the System;
- Provide the System as a service to third parties.

## 联系方式
sky_it_isec@163.com