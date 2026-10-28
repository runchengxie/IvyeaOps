# 后端测试与 Windows 兼容性

从 `server` 目录安装 `requirements.txt`、`requirements-test.txt`；MCP SDK 回归另装 `requirements-mcp-test.txt`。完整基础套件需要 IvyeaAgent，版本选择沿用 `.github/workflows/ci.yml` 的 release 规则。不要为了通过测试配置真实模型账号。

按 CI 的分组运行：

```powershell
python -m pytest tests -q --timeout=120 --timeout-method=thread
python -m pytest app/tests -q --timeout=180 --timeout-method=thread
```

默认 `python -m pytest` 也只收集这两个目录，不再收集应用中的 `settings_test.py::test_value` 业务函数。

测试进程在导入应用之前将 HOME、USERPROFILE、IVYEA_HOME、HERMES_HOME 和应用数据目录指向临时位置，并关闭 Agent 自动启动。只影响测试进程及其子进程，不改用户持久环境。需要特定配置的测试通过 monkeypatch 显式设置。

## 已覆盖的兼容边界

- 静态 JS/MJS：模拟错误的系统 MIME 注册表，验证实际 HTTP 响应为 `application/javascript`，测试应用运行在子进程以免污染后续路由。
- 项目路径：Windows 盘符、UNC 与 POSIX 的显示名；测试 DB 与真实写入一样使用规范化路径。
- 本地知识库：API 相对路径使用 `/`，实际文件操作和路径包含检查不变。
- 命令行假程序：用当前 Python 解释器运行测试脚本，保留真实子进程管道与 WebSocket 验证，不依赖 Bash 或 Windows 文件关联。
- 异步测试：同步辅助函数使用 `asyncio.run()` 自主管理循环，避免测试顺序依赖。

## Windows Hermes 会话同步

Windows 项目列表使用已有文件扫描器，不再启动 `hermes sessions export`。Windows CLI shim 超时后，其后代进程可能继续持有输出管道，导致 `subprocess.run` 的超时清理阶段仍然等待。

该路径只索引最近 14 天、最多 200 个会话文件，沿用原有内部会话过滤逻辑；这是索引覆盖限制，不保证整个目录枚举耗时有固定上限。POSIX 的 CLI 优先路径不变。仅在 CLI 数据库而未落入会话 JSON 的记录，不在 Windows 文件扫描覆盖内。

## PSD 依赖

应用使用自带 `psd_writer` 和 Pillow，已移除未使用的 psd-tools。已有环境请显式执行 `python -m pip uninstall psd-tools`（uv 环境可用 `uv pip uninstall psd-tools`），仅安装新的 requirements 不会自动卸载旧依赖。详见 [ADR-0038](decisions/0038-drop-unused-psd-tools.md)。

## 本轮验证（2026-10-28）

Windows / Python 3.12.13，测试依赖 IvyeaAgent 1.16.9：`tests` 904 passed / 1 skipped；`app/tests` 346 passed。跳过项为仅适用于 POSIX 的 master key 文件模式权限测试。现有 anyio/Pillow 弃用警告尚未清理。两组按上游 CI 分开执行；这些结果不等于已完成 Linux/macOS/Python 3.9 的本机验证。
