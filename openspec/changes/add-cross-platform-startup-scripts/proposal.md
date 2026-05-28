## 为什么

当前系统仅提供Windows PowerShell启动脚本（start.ps1），限制了在Linux和macOS等其他操作系统上的使用。为了支持跨平台部署和开发，需要添加Docker一键运行、Linux Shell脚本和Windows CMD脚本三种启动方式，使系统能够在任何主流操作系统上快速启动。

## 发生了什么变化

- 新增Docker一键运行支持：通过docker-compose.yml和相关配置文件，实现容器化部署
- 新增Linux Shell启动脚本（start.sh）：提供与start.ps1等价的Linux/macOS启动功能
- 新增Windows CMD启动脚本（start.cmd）：为不熟悉PowerShell的Windows用户提供替代方案
- 保持现有start.ps1脚本不变，作为Windows PowerShell用户的首选

## 能力

### 新增能力
- `docker-startup`：Docker容器化一键部署能力，支持通过docker-compose快速启动前后端服务
- `linux-startup`：Linux/macOS Shell脚本启动能力，提供bash/zsh兼容的启动脚本
- `windows-cmd-startup`：Windows CMD批处理启动能力，为CMD用户提供原生启动支持

### 修改的能力
<!-- 无需修改现有能力规格 -->

## 影响

- 新增文件：start.sh（Linux启动脚本）、start.cmd（Windows CMD启动脚本）
- 修改文件：docker-compose.yml（如需调整配置）
- 依赖项：Docker环境（用于容器化部署）、Python 3.11+环境（用于本地启动）、Node.js环境（用于前端开发服务器）
- 系统：支持Windows、Linux、macOS三大操作系统平台
