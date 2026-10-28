# eMAG 订单、退货、费用与库存证据

从 server 目录运行（与工作台使用同一个 `IVYEA_OPS_DATA_DIR`）：

```powershell
.venv/Scripts/python.exe -m app.emag_business_cli --store-id my-store-ro --days 29
```

使用现有 Windows 普通凭据 `IvyeaOps/eMAG/RO`。固定 RO 官方接口，仅调用 `product_offer/read`、`order/read`、`rma/read`、`invoice/read`、`vat/read`，不支持任意 URL 或平台写操作。请求继承进程代理配置，不跟随重定向、不自动重试，分页上限100页、每页100条，资源请求间隔1秒。

订单和退货分别显式读取 type=2（FBE）与type=3（卖家发货）；订单接口默认只返回type=3，不能省略这一分组。窗口限制1–29天。订单按创建时间、退货按申请日期、费用按发票日期读取。API日期过滤器无时区标记；当前发送UTC格式值并在证据与界面标记平台时区未核实，不能把边界记录当作已严格按店铺自然日对齐。

采集成功后保存一个不可变的组合快照，已有巡检页面自动展示经营证据。任何资源出现HTTP/业务错误、异常结构、重复/缺少身份、页数上限或发票总数不一致，则整轮不导入，原有完整快照保持不变。发票要求 `results.total_results` 与 `results.invoices`；VAT目录按非分页读取。

## 数据范围

- 商品：基本字段、平台价格状态、总库存字段、库龄分段，以及少量价格参照字段。参照价口径和商品规格未人工核对前不能用作目标售价。
- 订单：内部ID、类型、时间、状态、支付/退款状态与商品行数量/价格/税率等选定字段。
- 退货：内部ID、原订单关联、状态及商品数量等选定字段。申请不是退款支付证明。
- 发票：类别、编号、日期、原始金额/币种与storno标记。汇总不再次按storno反转符号，不等同于已付款。
- 排除客户/供应商身份对象、姓名、地址、电话、账号、附件链接、商品序列号和自由文本备注。仍包含敏感业务数据，应保持 data 目录私有。

## 库存与费用解释

`general_stock` 与 `stock_2p_aging_bands` 分别求已验证部分的小计，并统计缺失/无效观察数。没有有效观察时显示未知。逐SKU比较分段总和与库存字段；差额不能自动解释为预留、在途、损耗或丢货。该采集不替代后台FBE分仓、预留、在途和不可售台账。

费用按类别与币种保留原始Decimal正负号汇总。非法或缺失金额单独计数，界面明确标出部分覆盖；发票日期不等于服务期间，折扣也可能关联过去的促销。没有采购成本、费用归属和完整退款/结算对账，故 `profit=null`、`purchase_cost_status=missing`，不计算利润或推荐售价。

真实处理方案仍须人工核对成本、规格、税率与平台提示。当前工作台的批准/执行只是本地记录，不调用平台API写接口。

依据：[eMAG 官方 API 文档](https://marketplace-api.emag.ro/api-doc)、[FBE Stock 说明](https://marketplace.emag.ro/infocenter/emag-academy/fulfillment-by-emag/fbe-stock-manage-your-fbe-inventory-more-easily/?lang=en)。
