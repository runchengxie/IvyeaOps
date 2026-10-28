# eMAG 工作台与手动无头巡检

运行后端使用的同一 Python 环境和同一 `IVYEA_OPS_DATA_DIR`，在 `server` 目录执行。无需浏览器、console 页面或模型进程保持开启；联网采集仍需要网络、可用的 eMAG 权限和 IP 白名单。

```powershell
# 新只读采集 → 与运行前快照比较 → 本地报告 → 回执
.venv/Scripts/python.exe -m app.emag_job_cli --store-id demo-ro --days 29
# 无凭证、无网络的已有快照重放，不宣称发生了新采集/变化
.venv/Scripts/python.exe -m app.emag_job_cli --store-id demo-ro --from-latest
# 查看人工处理记录；此命令不操作平台
.venv/Scripts/python.exe -m app.emag_workflow_cli --store-id demo-ro
```

Windows 采集从普通凭据 `IvyeaOps/eMAG/RO` 读取用户名密码，沿用 [只读采集说明](emag-readonly.md)。Linux 等环境可以先显式导入快照再离线运行。不要把凭证放在命令参数、仓库或报告里。店铺标签需使用自己的已导入标签，示例 `demo-ro` 不会自动匹配实际店铺。

不会注册操作系统定时任务。每个店铺同一时间只有一个该入口任务；冲突会退出，避免重复请求。退出码 0 表示报告与回执保存成功，1 表示某阶段失败，2 表示参数/存储/运行锁不可用。失败回执只保留异常类型，不保留异常原文。采集失败不导入新快照；若发布后报告失败，回执会指出已发布的快照。进程被强行中止时，不保证有新回执，必须检查回执运行时间，不能把旧成功当作本次成功。

回执位于私有数据目录 `store-artifacts/jobs/<store>/`，包含来源版本、基线版本、运行模式、字段变化、报告 ID 和时间。`ivyea_emag_job_status` 是只读 MCP 工具，只读取最近已完成/失败回执，不启动采集。`ivyea_report_read` 可按回执报告 ID 读取报告和绑定的快照。

增量比较商品 ID、售价、库存和审核状态。数字 10 与字符串 "10.00" 视为相同数值，缺失库存与 0 区分。新增/缺失商品只是观测变化，不等于平台已经上架/下架。首次采集和离线重放没有可用变化基线。回执保留变化总数及最多 200 项、64 KB 的变化预览，明确标记是否截断；完整内容可从引用的两份不可变快照比较，避免大量审核文字使回执超限。

## 页面能力

| 入口 | 当前 eMAG 能力 | 需要补齐的能力或限制 |
|---|---|---|
| 任务台 | RO/RON、ID/SKU/PNK、来源和未知字段约束 | 对话需要模型；不是巡检运行依赖 |
| eMAG 巡检 | 商品异常、经营证据、人工处理和新版本复查 | 审批记录不会调用写 API |
| 运营驾驶舱 | 实际商品、订单数量、库存库龄字段与异常 | 成本未补前不计算利润或建议售价 |
| 市场调研 | 本店类目结构、商品搜索、带版本的人工调研记录 | 不是全市场份额/销量/关键词搜索量 |
| 打法推荐 | 按库存和异常给出核查优先级、保存方案草稿 | 不自动执行改价、补货、申诉 |
| Listing | 选择真实商品、保存版本绑定的本地文案草稿 | 不编规格、不自动翻译或提交平台 |
| 图片翻译 | 增加 RO/BG/HU，默认选择 RO | 需要图片模型和人工复核 |
| 分析工具 | 缺失字段、巡检状态、增量和报告引用 | 未知不是零；旧回执不代表当前资料 |
| 知识库 | eMAG 商品/调研/复查模板 | 保留已有文件及原平台模板 |
| 外部智能体 | 通用 agent 配置，读取快照与回执的 MCP | 原 Amazon 关键词工具不支持 eMAG |
| 终端 / 监控 | 手动 CLI 用法、本机服务状态 | 监控不证明 eMAG API 正常 |
| 头程比价 | 继续使用自有报价导入和比较 | 必须提供真实 RO 线路，不能套用其他目的国报价 |
| 用户管理 | 本机用户与权限 | 独立于 eMAG 凭证管理 |
| 资讯 | 官方来源链接入口 | 不抓取或伪装成最新 eMAG 新闻流 |

核心业务页和草稿 API 使用管理员权限。旧平台页面保留在 `/legacy/dashboard`、`/legacy/market`、`/legacy/playbook`、`/legacy/listing`、`/legacy/tools`、`/legacy/news`，默认入口使用 eMAG；这些旧功能仍适用于原平台。

## 本地草稿与人工流程

草稿保存在私有 `emag-workspace.sqlite3`，绑定 store/snapshot/product。Listing 必须选择该版本实际存在的商品。来源已更新时拒绝保存旧版本，历史草稿标为待重新核对。草稿目前是追加记录，不是平台 Listing 编辑器。

人工状态只能按 pending → proposed → approved → executed → reviewed 顺序记录，需明确来源快照、异常 ID、当前 revision 和说明。例：

```powershell
.venv/Scripts/python.exe -m app.emag_workflow_cli --store-id demo-ro --snapshot-id VERSION --issue-id ISSUE --state proposed --revision 0 --note "核实平台拒绝原因，暂不改价"
```

复查另需 `--review-snapshot-id NEW_VERSION`，且必须是明确检查过的更新快照。`executed` 仅记录实际人工操作，不会代你调用 eMAG。这轮没有自动批准、平台写接口或定时运行。
