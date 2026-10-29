# 安装与源码目录迁移

[英文权威版本](../installation.md)

安装脚本接受 Python 3.11+ 和 Node.js 20+，CI 构建使用 Node.js 22。本机验证环境为 Windows、Python 3.12.13、Node.js 24.22.1；CI 配置 Linux、Windows、macOS，不代表某个提交已在这些环境实际运行。

运行环境、test 和可选 MCP test requirements 分别位于 `src/server`。安装脚本、CI 和发布构建默认使用 `configs/ivyea-agent.ref` 中的 IvyeaAgent 标签，目前为 `v1.16.9`。显式设置 `IVYEA_AGENT_REF` 可以覆盖默认值。已有安装、本地或打包的 Agent 源码可能使用不同版本；Git 标签并非不可变。不要假设此 fork 已发布二进制包。

Windows 源码安装和启动：

```powershell
powershell -NoProfile -File scripts/manage.ps1 -Action install -Target source
powershell -NoProfile -File scripts/manage.ps1 -Action start -Target source
```

英文双击入口在 `scripts/`。根目录存在 `IvyeaOpsServer.exe` 时，`install.bat` 才选择免 Python 包。`start.bat` 为前台，`start-hidden.vbs` 为后台，`start-lan.bat` 是显式源码 LAN 模式，不自动修改防火墙。

Linux/macOS 使用 `bash scripts/manage.sh install` 和 `bash scripts/manage.sh start`。安装器可能安装依赖、构建前端或提供可选组件，不能当作验证命令。Unix 前台用 Ctrl+C 停止，或管理自己的 systemd 服务。

## 旧源码安装

不再支持 Python 3.9 和 3.10。安装 Python 3.11 或更新版本，停止应用，并在重新运行安装器前将旧的 `src/server/.venv` 移到备份位置。安装器不会复用旧环境；请保留 `src/server/.env`、凭证和数据目录，重启前检查自定义服务路径。

跟踪目录从 `client`、`server` 迁为 `src/client`、`src/server`。Git 不会搬走其他工作区的 ignored 文件。新环境文件缺失时，运行环境兼容读取旧 `server/.env`；安装器只在新文件不存在时复制，保留旧文件，不覆盖已有新配置。

用新安装器创建或复用虚拟环境。其他机器或位置的 venv 不是可移植产物。保留 `data` 和自己的 `IVYEA_OPS_DATA_DIR`，检查手工快捷方式、服务和部署路径。

systemd 的 WorkingDirectory 仍为 `<repository>/server` 时，安装/更新会停止并提示迁移，而不重启错误路径。先用 `systemctl cat ivyea-ops.service` 检查并备份 unit，保留用户、端口和自定义参数。将 WorkingDirectory、PYTHONPATH 改为 `<repository>/src/server`，Python 可执行文件改为 `<repository>/src/server/.venv/bin/python`。执行 `sudo systemctl daemon-reload`，安装新环境，核对后再重启。不要用默认模板直接覆盖自定义服务。

冻结 Windows/macOS 包仍保留内部 `client`、`server` 布局。`scripts/update-bundle.bat` 只用于 Windows 冻结包，没有兼容 release 和备份时不要用上游包覆盖自定义 fork。

## 开发检查

```bash
cd src/client
npm ci
npm run typecheck
npm run test:i18n
npm run build
```

进入 `src/server` 创建并激活本平台 venv，安装 `requirements.txt`、`requirements-test.txt`、`requirements-mcp-test.txt`，执行 `python -m pytest`。FastAPI 生产页面需要已构建前端。Vite development 为 5174，后端为 8001，隔离组件 harness 为 5199。

仓库不再提供 Docker 部署文件或 Docker 安装命令。已有容器部署需要自行维护配置。除审计证据明确列出外，本地审计没有执行 systemd 修改或二进制发行包组装。
