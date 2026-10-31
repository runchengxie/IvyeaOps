# eMAG 写入 API 的准备工作

[英文权威版本](../emag-write-readiness.md)

现有工作台记录本地方案及人工操作，其批准仍不会提交更改。独立管理员API支持通过 `/offer/save` 提交明确批准的单商品RON税前 `sale_price` 修改，默认关闭执行，没有前端提交按钮或MCP平台写工具。

## 单商品价格 API

真实执行要求服务器启动时同时配置 `IVYEA_OPS_EMAG_WRITES_ENABLED=1` 和 `IVYEA_OPS_EMAG_WRITE_STORE_ID=example-ro`。店铺标签必须对应现有Windows通用凭据 `IvyeaOps/eMAG/RO` 的准确账号，仍需API权限及IP白名单，不需要浏览器登录。单独启用配置不会提交修改。`example-ro`及下面的价格均为占位示例，不是店铺建议。

所有路由要求现有管理员会话。基础路径为 `/api/emag/stores/{store_id}/api-changes`。

| 方法及后缀 | 请求 | 结果 |
|---|---|---|
| `GET` 基础路径 | 无 | 最近100个提议及实际执行开关 |
| `POST` 基础路径 | `snapshot_id`、字符串 `product_id`、`changes: {"sale_price":"24.5"}` | 本地新旧值预览及SHA-256 `digest` |
| `POST /{proposal_id}/approve` | 精确 `digest`、`note` | 独立批准该项具体提议 |
| `POST /{proposal_id}/execute` | 精确 `digest`、JSON布尔值 `confirmed: true` | 实时预检、最多一次提交、回读及持久回执 |
| `POST /{proposal_id}/reconcile` | 无 | 只读复查，不重发 |

准备及批准不读取平台凭据、不联网。价格必须有限、为正、在已观察的卖家边界内，最多四位小数。拒绝无变化请求、其他字段、不明确ID及旧快照。轻量接口不套用商品资料接口中存在矛盾的ID上限。实时核对ID、SKU、PNK、币种、原价及卖家边界；预检期间快照更新也会阻止提交。请求只发送单项 `data` 数组中的 `id` 和 `sale_price`，禁止重定向及自动重试写入。

`verified` 只表示价格回读一致，不等于恢复可售、发布、成交或结算回款。`submitted_unverified` 表示API接受但回读未匹配，可只读复查。`uncertain` 表示送达或接受未知；即使后续读到目标价，也不能证明该次尝试被接受，因此仍阻止同商品后续提交，需人工查明。中断留下的 `submitting` 也不允许重发，至少等待120秒后才可复查。不假定回滚或自动解决不确定状态。下次改动前应重新采集完整快照。

私有回执和只追加审计事件保存在 `emag-api-changes.sqlite3`，只记录有界状态及响应哈希，不保留凭据或原始平台响应。现有异常审批、本地草稿及MCP权限语义不变。商品资料、库存、上下架及订单写入仍不支持；资料归属、已有商品更新和字段删除语义需核实。开发测试使用虚构商品及模拟HTTP，没有执行真实写入或无变化写入探测。

[eMAG API 文档入口](https://marketplace.emag.ro/infocenter/emag-academy/how-to-add-a-product/product-import-through-api-or-feeds/api-documentation/?lang=en)介绍了通过 API 导入商品和处理订单。[卖家入驻指南](https://marketplace.emag.ro/infocenter/emag-academy/i-want-to-be-an-emag-marketplace-partner/?lang=en)介绍了上架前提和商品管理。[当前 API 参考文档](https://marketplace-api.emag.ro/api-doc)列出了用于创建或更新商品及报价的 `POST /api-3/product_offer/save`，以及用于更新已有报价字段的 `POST /api-3/offer/save`，并说明需要 HTTP Basic 认证、IP 白名单和 API 权限。文档还提示，资料错误返回 `isError: true` 时，新报价仍可能被保存并处理。实施或使用前须核对当前请求结构、账号权限和实际行为；尤其不能把错误响应视为没有发生写入的证明。价格验证和具体类目的更新行为仍未核实。

考虑写入前：

1. 核实端点和请求结构、账号权限、支持的市场、类目要求及是否存在测试环境。不能假定仅做验证就是安全的试运行。
2. 按商品预览店铺、商品标识、来源快照、新旧值和理由。拒绝使用过期或含糊的证据，对具体变更要求明确确认。
3. 在确认 API 实际语义后，确定逐商品回执、审计记录、部分失败处理和安全重试策略。不能假定接口支持幂等或回滚。
4. 经核实的人工操作或未来支持的写入完成后，重新采集只读证据，检查平台状态。请求被接受不代表商品已上架。

这些检查不证明真实账号权限或恢复价格。
