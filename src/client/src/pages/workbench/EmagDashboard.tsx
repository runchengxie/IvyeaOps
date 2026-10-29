import { useState } from 'react';
import { Link } from 'react-router-dom';
import { dashboardMetrics } from './emagDashboardData.mjs';
import './emag-dashboard.css';

type DashboardData = {
  store_id: string; captured_at: string; source: string; snapshot_id: string;
  summary: Record<string, unknown>;
  offers: { id: string | number; name?: string; part_number?: string }[];
  issues: { issue_id: string; id: string | number; reason: string; general_stock: number | null }[];
  commercial_summary?: { orders_fbe_count: number; orders_seller_count: number; invoice_count: number;
    window?: { start: string; end: string; timezone_note?: string };
    inventory: { general_stock_total: number | null; aging_total: number | null; mismatched_skus: number } };
};

const labels: Record<string, string> = { invalid_price: '价格无效', documentation_rejected: '资料拒绝', blocked: '平台受阻' };

export default function EmagDashboard({ data }: { data: DashboardData }) {
  const [view, setView] = useState<'management' | 'specialist'>('management');
  const metrics = dashboardMetrics(data);
  const items = [
    { label: '商品记录', value: metrics.offers, unit: '条', note: '当前快照' },
    { label: '窗口内订单', value: metrics.orders, unit: '单', note: 'FBE + 自发货' },
    { label: '已知库存小计', value: metrics.stock, unit: '件', note: '平台库存字段' },
    { label: '观测到的异常', value: metrics.issueCount, unit: '项', note: '按异常原因统计' },
    { label: '费用 / 折扣单据', value: metrics.invoices, unit: '张', note: '不等于实际付款' },
    { label: '利润', value: null, unit: '', note: '采购成本待补' },
  ];
  return <div className="ed-dashboard">
    <div className="ed-toolbar"><div className="ed-switch" aria-label="驾驶舱视角">
      <button type="button" aria-pressed={view === 'management'} onClick={() => setView('management')}>管理视角</button>
      <button type="button" aria-pressed={view === 'specialist'} onClick={() => setView('specialist')}>专员视角</button>
    </div><span className="ed-market">eMAG RO</span><span className="ed-time">采集时间 {new Date(data.captured_at).toLocaleString()}</span></div>
    {view === 'management' ? <>
      <section className="ed-panel" aria-label="核心指标"><div className="ed-panel-head"><div><h2>核心指标</h2><p>来自本店已采集的证据</p></div><span className="ed-badge">快照数据</span></div>
        <div className="ed-grid">{items.map(item => <div className="ed-card" key={item.label}><span>{item.label}</span><strong>{item.value ?? '未接入'}<small>{item.value == null ? '' : item.unit}</small></strong><p>{item.note}</p></div>)}</div>
        <div className="ed-source">数据来源：{data.source} · 快照 {data.snapshot_id}。{data.commercial_summary?.window ? `订单筛选窗口：${data.commercial_summary.window.start} — ${data.commercial_summary.window.end}（平台时区尚未核实）。` : '订单筛选窗口未采集。'}订单数量不等于成交金额。</div>
      </section>
      <section className="ed-panel" aria-label="运营关注"><div className="ed-panel-head"><div><h2>运营关注</h2><p>先核对高优先级商品，再记录处理方案</p></div><Link to={`/emag?store=${encodeURIComponent(data.store_id)}`}>查看巡检 →</Link></div>
        <div className="ed-grid ed-grid-actions"><div className="ed-card"><span>有库存且价格无效</span><strong>{metrics.priceWithStock}<small>项</small></strong><p>核对价格与成本</p></div><div className="ed-card"><span>资料被拒</span><strong>{metrics.documentationRejected}<small>项</small></strong><p>查看平台审核说明</p></div><div className="ed-card"><span>平台受阻</span><strong>{metrics.blocked}<small>项</small></strong><p>核实后台原因</p></div><div className="ed-card"><span>广告数据</span><strong>未接入</strong><p>不展示推算数据</p></div></div>
        <div className="ed-source">以上为已观察到的异常数量；价格状态未知 {metrics.priceUnknown ?? '未核实'} 条 · 资料状态未知 {metrics.documentationUnknown ?? '未核实'} 条 · 库存未知 {metrics.stockUnknown ?? '未核实'} 条。成本、利润和广告数据尚未接入；快照不是平台实时状态。</div>
      </section>
    </> : <section className="ed-panel" aria-label="异常商品"><div className="ed-panel-head"><div><h2>异常商品</h2><p>按当前快照的异常原因列出，处理进度请进入巡检查看</p></div><Link to={`/emag?store=${encodeURIComponent(data.store_id)}`}>进入巡检 →</Link></div>
      {data.issues.length ? <div className="ed-table-wrap"><table className="ed-table"><thead><tr><th>商品 / SKU</th><th>异常</th><th>库存字段</th><th>操作</th></tr></thead><tbody>{data.issues.slice(0, 50).map(issue => {
        const offer = data.offers.find(item => String(item.id) === String(issue.id));
        return <tr key={issue.issue_id}><td>{offer?.name || issue.id}<small>{offer?.part_number || 'SKU 未采集'}</small></td><td><span className="ed-issue">{labels[issue.reason] || issue.reason}</span></td><td>{issue.general_stock ?? '未知'}</td><td><Link to={`/emag?store=${encodeURIComponent(data.store_id)}&issue=${encodeURIComponent(issue.issue_id)}`} aria-label={`查看 ${offer?.part_number || issue.id} 异常`}>查看详情 →</Link></td></tr>;
      })}</tbody></table>{data.issues.length > 50 && <p>仅显示前 50 项，请进入巡检查看完整清单。</p>}</div> : <p>当前快照未观察到已跟踪的异常。</p>}
      <div className="ed-source">未观察到异常不代表所有经营风险已排除。价格状态未知 {metrics.priceUnknown ?? '未核实'} 条 · 资料状态未知 {metrics.documentationUnknown ?? '未核实'} 条 · 库存未知 {metrics.stockUnknown ?? '未核实'} 条。</div>
    </section>}
  </div>;
}
