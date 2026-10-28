# 外部 Agent 调用工作台

本地 fork 的第一阶段允许外部 Agent 通过 MCP 使用资料与报告功能，无需给工作台配置聊天模型。原有关键词工具仍需数据源；知识库仍依赖 IvyeaAgent，不能据此声称所有功能已脱离内置 Agent。

## 当前能力

入口为 `http://127.0.0.1:8001/api/mcp`，使用 Bearer 令牌，支持 HTTP JSON 响应。客户端必须支持 Streamable HTTP。网页的本机免登录不取消 MCP 令牌校验。

| 工具 | 权限 | 行为 |
|---|---|---|
| `ivyea_health` | read | 检查版本和集成状态 |
| `ivyea_store_snapshot` | read | 根据 store_id 读取最近导入的快照 |
| `ivyea_report_save` | write | 保存本地报告，并内嵌指定 snapshot_id 的快照证据 |
| `ivyea_report_read` | read | 根据 report_id 读取报告 |

工具不连接 eMAG；没有快照会明确报错。报告写权限只用于本地文件，未增加调价、上架或订单写工具。令牌的 write scope 仍沿用项目现有权限模型，后续扩大写工具范围前应进一步拆分权限。

## 导入资料

eMAG RO 商品可通过[只读采集 CLI](./emag-readonly.md)直接生成快照与摘要；以下方式适用于手动整理或其他来源的数据。MCP 本身仍只访问本地资料，不读取卖家凭据。

从 `server` 目录运行：

```powershell
.venv/Scripts/python.exe -m app.store_cli import-snapshot ../data/my-snapshot.json
```

格式示例（仅说明结构，不能当作店铺证据）：

```json
{
  "store_id": "demo-emag-ro",
  "platform": "emag",
  "marketplace": "RO",
  "captured_at": "2026-10-28T02:00:00Z",
  "source": "demo-only",
  "coverage": ["dashboard"],
  "limitations": ["Synthetic example; not a real store"],
  "data": {"seller_rating": 4.9}
}
```

字段须显式填写，时间必须有时区。快照为追加保存，写完后原子发布；最新指最后导入的版本，不代表采集时间最近。读取时返回 snapshot_id，保存报告必须携带这个版本 ID，报告附入该版本快照，避免并发导入导致证据错配。数据存于 `data/store-artifacts`，不会进入 Git。CLI 与服务必须指向同一个 `IVYEA_OPS_DATA_DIR`。

## 连接客户端

在工作台令牌管理接口 `/api/mcp-admin/tokens` 创建 read 令牌；保存报告需要显式授予 read、write。明文令牌仅返回一次，不要写进版本库。读取快照会把快照内容交给调用方，外部模型的数据处理政策仍适用。

Codex 配置示例，**令牌由启动客户端时的环境变量提供**：

```toml
[mcp_servers.ivyea_ops]
url = "http://127.0.0.1:8001/api/mcp"
bearer_token_env_var = "IVYEA_MCP_TOKEN"
```

Hermes 或其他 Harness 需按各自客户端版本配置 HTTP MCP URL 和 Authorization Header；尚未逐一验证，不保证可以直接套用 Codex 的配置。

不要把工作台全部 REST 管理接口包装成 Agent 工具。外部调用保留窄工具、独立令牌与审计。当前本机免登录服务不能直接开放到公网；远程访问应另设计认证和传输。

## 最小验收任务

连接 → `ivyea_health` → `ivyea_store_snapshot` → 检查来源、时间和缺失范围 → 在外部 Agent 分析 → `ivyea_report_save` → `ivyea_report_read` 核对结果。

## 无头运行

网页可以关闭，后台 HTTP 服务与 MCP 仍可运行。外部 Agent 无需打开 `/console`，也不必先给工作台配置聊天模型。当前仍启动整个 FastAPI 服务，并未拆成独立轻量 MCP-only 进程。先使用一个已有 Harness 验证流程；是否增加 DeepSeek Harness、独立调度器或插件，等真实任务提出需求再决定。

操作指引见 `skills/emag/store-audit/SKILL.md`，先按文档阅读或手动安装到所选 Harness，项目不会自动修改你的全局 Agent 配置。

## 开发验证

在独立虚拟环境中安装 `requirements.txt` 和可选的 `requirements-mcp-test.txt`，从 server 目录运行：

```powershell
.venv/Scripts/python.exe -m pytest app/tests/test_store_artifacts.py app/tests/test_mcp_server.py app/tests/test_mcp_sdk.py
```

SDK 回归测试使用本地 ASGI transport，不连接店铺或模型。ERP 和市场数据候选的核对记录见 [emag-data-sources.md](./emag-data-sources.md)。
