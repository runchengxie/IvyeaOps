# eMAG 数据与执行系统候选

核对日期：2026-10-28。这里只记录接入选择，不表示已经授权或连接任何服务。

| 候选 | 已核实的用途 | 对本 fork 的角色 | 待核实 |
|---|---|---|---|
| eMAG 官方 API | 商品与报价、库存、订单管理 | 自店数据直连候选 | 账号 API 权限、IP 许可、当前接口契约 |
| Base.com / BaseLinker | eMAG 刊登、订单、库存价格同步；公开 API 有订单与库存读取方法 | 多平台 ERP 与履约执行候选 | 套餐、账号权限、eMAG 特定字段是否在 API 开放 |
| easySales | eMAG RO/BG/HU 订单、刊登、库存价格同步；提供外部 API | eMAG 多站点 ERP 候选 | API 具体范围、套餐、限流、历史订单覆盖 |
| 店小秘 | 本轮未取得足够明确的官方 eMAG 文档 | 暂保留候选 | VIP、订单处理与库存同步的当前支持范围 |
| MASAT | X Scan 与 MCP Connector | 市场研究候选 | MCP 鉴权和兼容性、是否有自店数据工具 |
| LinkFox | 官方 API Skills 覆盖调研与图文视频工具 | 可选内容与调研能力 | eMAG 原生工具尚未确认，额度及数据出境范围 |

## 接入原则

多个系统可以提供不同资料，但库存、价格和订单状态各自应明确唯一主系统。尤其 easySales 官方说明，关联报价后由 easySales 推送库存和价格；若同时让另一个 ERP 或 Agent 直改，会出现覆盖风险。

外部 Agent → IvyeaOps MCP → 经明确选择的数据源或 ERP 适配器。第一阶段先读数据；新增具体店铺写工具时，再定义范围、审批与可核对的执行结果。无需为了验证第一阶段就购买或绑定多个 ERP。

目前快照格式只是携带来源的通用证据容器，并未完成各家 API 的字段标准化或实时同步。

## 官方资料

- [Base.com eMAG integration](https://base.com/pl-PL/pomoc/wiedza/emag/)
- [Base API](https://api.base.com/)，[getOrders](https://api.base.com/index.php?method=getOrders)
- [easySales eMAG integration guide](https://easy-sales.com/en/guides/connect-emag-with-easysales)
- [easySales API integration](https://easy-sales.com/us/website/api)
- [eMAG API import](https://marketplace.emag.hu/infocenter/emag-academy/api-documentation/the-api-import/?lang=en)
- [MASAT](https://masat.ro/)
- [LinkFox Skills](https://github.com/linkfox-ai/linkfox-skills)
