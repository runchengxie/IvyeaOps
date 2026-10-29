# eMAG RO 只读商品采集

需要订单、退货、费用及库龄证据时，另见[组合采集命令](emag-business-evidence.md)；以下基础命令仅采集商品。

从 `src/server` 目录运行，使用现有 Python 环境和 `requirements.txt`。仅支持罗马尼亚站，固定调用官方 HTTPS `product_offer/read`。不支持上架、改价、库存写入或订单处理，不需要内置模型或打开 `/console`。

## 首次配置

需要有效的 eMAG API 账号权限和出口 IP 白名单。网页能登录不等于 API 能访问。

Windows 用户在“凭据管理器 → Windows 凭据 → 添加普通凭据”保存：

- 网络地址：`IvyeaOps/eMAG/RO`
- 用户名、密码：有 API 权限的卖家账号

西班牙语对应 `Administrador de credenciales → Credenciales de Windows → Agregar una credencial genérica`。不是“Agregar una credencial de Windows”。脚本通过 [CredReadW](https://learn.microsoft.com/windows/win32/api/wincred/nf-wincred-credreadw) 只读取这一条，不枚举其他凭据。删除或编辑该项即可撤销或更新；同一 Windows 登录用户下的程序也可能读取凭据。换机器、用户或服务账号时需重新配置。

## 运行

```powershell
# 与运行中的工作台使用相同的数据目录；替换为自己的绝对路径
$env:IVYEA_OPS_DATA_DIR = 'C:\path\to\IvyeaOps\data'
.venv/Scripts/python.exe -m app.emag_cli --describe
.venv/Scripts/python.exe -m app.emag_cli --store-id my-store-ro
```

`store-id` 是本地证据标签，不是 API 登录名；不会自动核实账号属于哪个店铺。相同凭据目标一次表示一个 RO 账号。多账号隔离尚未实现。

Linux/macOS 或不使用凭据库时，在交互终端加 `--prompt`，密码通过隐藏输入获得，不持久化。默认模式缺少凭据直接退出，不会让无人值守任务挂在输入框。

请求继承进程代理环境，不修改用户级代理设置。标准运行依赖已包含 SOCKS 支持；`requirements-emag-socks.txt` 为旧安装保留兼容入口。出口 IP 必须与 eMAG 白名单一致。

## 输出与边界

- 每页 100 条，最多 100 页，分页间隔 1 秒；无自动重试，不跟随重定向。
- 遇到 HTTP/业务/格式错误、重复或缺少商品 ID、页数上限立即停止。退出码 1 表示不完整，未导入；退出码 2 表示配置、凭据或本地保存错误；0 表示已保存快照与报告。
- 成功输出 JSON，包含 `snapshot_id`、`report_id` 和条数。可用 `python -m app.store_cli read-report REPORT_ID` 或 MCP 工具读取；MCP 工具本身不会触发采集。
- 数据在配置的 `data/store-artifacts` 追加保存。Git 忽略默认 data 目录；自定义目录请自行确保不会提交到仓库。CLI不记录密码、认证头或原始响应全文。
- 保留商品标识、价格、库存字段、审核状态与简短错误，省略可能嵌入完整商品资料的嵌套审核错误。快照和报告分别限制 2 MB；超限退出，不分拆成伪装完整的快照。若报告保存失败，已经成功写入的快照可能仍存在。
- “完整”仅表示分页正常结束，页面之间并非原子快照。`status=1` 不保证前台可售；缺失库存计为未知，FBE库存需另行核对。不同问题组可能重叠。
- 摘要标出价格无效、资料审核拒绝与 Blocked，并在快照中提供具体 SKU。价格为 API 原值，未做含税换算；不推断销量、利润或损失。

官方接口和状态依据：[eMAG Marketplace API](https://marketplace-api.emag.ro/api-doc)。

## 本地开发验证

先安装 `requirements.txt`、`requirements-test.txt` 和 `requirements-mcp-test.txt`。`src/server/pytest.ini` 将默认发现范围限制为 `tests` 和 `app/tests`，避免把设置连通性业务函数当作测试。完整 `tests` 套件另需安装上游 CI 所用的 IvyeaAgent；它不是 eMAG CLI 运行依赖。

```powershell
.venv/Scripts/python.exe -m pytest app/tests/test_emag_readonly.py app/tests/test_store_artifacts.py app/tests/test_mcp_server.py app/tests/test_mcp_sdk.py
```

测试使用合成数据和 HTTP mock，不需要真实凭据。尚未配置定时调度，操作系统任务或 agent 可按需调用该 CLI。
