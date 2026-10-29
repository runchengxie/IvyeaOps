# eMAG 写入 API 的准备工作

[英文权威版本](../emag-write-readiness.md)

本文是评估清单，项目尚未实现平台写入集成。当前流程采集证据，并在本地记录方案和人工操作；批准不会提交更改。

[eMAG API 文档入口](https://marketplace.emag.ro/infocenter/emag-academy/how-to-add-a-product/product-import-through-api-or-feeds/api-documentation/?lang=en)介绍了通过 API 导入商品和处理订单。[卖家入驻指南](https://marketplace.emag.ro/infocenter/emag-academy/i-want-to-be-an-emag-marketplace-partner/?lang=en)介绍了上架前提和商品管理。[当前 API 参考文档](https://marketplace-api.emag.ro/api-doc)列出了用于创建或更新商品及报价的 `POST /api-3/product_offer/save`，以及用于更新已有报价字段的 `POST /api-3/offer/save`，并说明需要 HTTP Basic 认证、IP 白名单和 API 权限。文档还提示，资料错误返回 `isError: true` 时，新报价仍可能被保存并处理。实施或使用前须核对当前请求结构、账号权限和实际行为；尤其不能把错误响应视为没有发生写入的证明。价格验证和具体类目的更新行为仍未核实。

考虑写入前：

1. 核实端点和请求结构、账号权限、支持的市场、类目要求及是否存在测试环境。不能假定仅做验证就是安全的试运行。
2. 按商品预览店铺、商品标识、来源快照、新旧值和理由。拒绝使用过期或含糊的证据，对具体变更要求明确确认。
3. 在确认 API 实际语义后，确定逐商品回执、审计记录、部分失败处理和安全重试策略。不能假定接口支持幂等或回滚。
4. 经核实的人工操作或未来支持的写入完成后，重新采集只读证据，检查平台状态。请求被接受不代表商品已上架。

本清单没有实现或执行平台写入。
