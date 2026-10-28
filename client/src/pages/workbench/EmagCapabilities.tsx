import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';

const capabilities=[
  {title:'只读店铺巡检',to:'/emag',scope:'已实现 · 人工处理记录',description:'读取 RO 商品异常、订单/退货/费用证据；按库存优先核查。批准记录不会调用平台写接口。'},
  {title:'经营证据与分析',to:'/dashboard',scope:'已实现 · 已采集快照',description:'查看商品、订单数量、库存库龄与费用字段。成本待补；不据此计算利润或推荐售价。'},
  {title:'Listing 本地草稿',to:'/listing',scope:'已实现 · 本地保存',description:'选择快照中的真实商品，起草文案。绑定来源版本；更新后的旧证据不能直接保存。不会提交平台。'},
  {title:'本店调研与方案',to:'/market',scope:'已实现 · 本店资料',description:'本店类目结构、调研记录与打法草稿。全市场搜索量、竞品销量和份额尚未接入。'},
  {title:'图片本地化',to:'/image-translate',scope:'需要图片模型',description:'支持 RO/BG/HU。需要配置图片服务并人工核对文字和规格，不自动上架。'},
  {title:'eMAG 知识模板',to:'/brain?tab=templates',scope:'已实现 · 本地知识库',description:'商品证据、调研和处理复查模板。记录 SKU/PNK、来源、采集日期与未知事项。'},
];

type Store={store_id:string;captured_at?:string};
type Receipt={status:string;mode:string;stage:string;snapshot_id?:string;report_id?:string;finished_at?:string};
export default function EmagCapabilities({isAdmin}:{isAdmin:boolean}){
  const [stores,setStores]=useState<Store[]|null>(null),[store,setStore]=useState(''),[error,setError]=useState('');
  const [receipt,setReceipt]=useState<Receipt|null>(null),[receiptState,setReceiptState]=useState('');
  useEffect(()=>{if(!isAdmin)return;let alive=true;api.get('/emag/stores').then(r=>{if(alive){setStores(r.data);setStore(r.data[0]?.store_id||'');}}).catch(()=>{if(alive)setError('店铺来源读取失败，不能判断是否有资料。');});return()=>{alive=false;};},[isAdmin]);
  useEffect(()=>{setReceipt(null);setReceiptState('');if(!isAdmin||!store)return;let alive=true;setReceiptState('正在读取回执…');api.get(`/emag/stores/${encodeURIComponent(store)}/job`).then(r=>{if(alive){setReceipt(r.data);setReceiptState('');}}).catch(e=>{if(alive)setReceiptState(e.response?.status===404?'尚无手动巡检回执。':'回执读取失败，请稍后重试。');});return()=>{alive=false;};},[isAdmin,store]);
  const selected=stores?.find(s=>s.store_id===store);
  const label=/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(store)?store:'YOUR_STORE_ID';
  return <div style={{padding:'14px 16px',lineHeight:1.7,overflowWrap:'anywhere',minWidth:0}}>
    <h2>eMAG 已实现能力</h2><p>此目录列出本 fork 已实现的功能和运行条件。无需从社区安装；需要模型的项目单独标明。</p>
    <section className="cap-section"><h3>本机证据状态</h3>{!isAdmin?<p>管理员可查看本机店铺来源和巡检回执。此处不读取店铺资料。</p>:<>
      {error?<p role="alert">{error}</p>:stores===null?<p>正在读取来源…</p>:<p>已导入 {stores.length} 个店铺来源。这表示存在本地快照，不证明 API 凭证当前可用。</p>}
      {!!stores?.length&&<><label>巡检店铺 <select aria-label="巡检店铺" value={store} onChange={e=>setStore(e.target.value)}>{stores.map(s=><option key={s.store_id}>{s.store_id}</option>)}</select></label><p>来源采集时间：{selected?.captured_at?new Date(selected.captured_at).toLocaleString():'未提供'}</p>{receipt?<><p>最近回执：{receipt.status} · {receipt.mode} · 阶段 {receipt.stage}</p><p>完成时间：{receipt.finished_at?new Date(receipt.finished_at).toLocaleString():'未提供'} · 绑定版本：{receipt.snapshot_id||'未生成'}</p><p>回执仅说明该次任务的结果，不保证对应当前最新资料。<Link to="/tools">核对当前版本与变化</Link></p></>:<p role="status">{receiptState}</p>}</>}
    </>}</section>
    <div className="cap-grid">{capabilities.map(c=><section className="cap-card" key={c.to}><h3>{c.title}</h3><span className="cap-dim">{c.scope}</span><p>{c.description}</p>{isAdmin?<Link to={c.to}>打开功能</Link>:<span>管理员可使用</span>}</section>)}</div>
    <section className="cap-section"><h3>手动无头入口</h3><p>在 server 目录使用后端同一 Python 环境、同一 IVYEA_OPS_DATA_DIR。联网采集需 eMAG 权限及 Windows 普通凭据 IvyeaOps/eMAG/RO；此页不读取或验证密码。</p><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{`python -m app.emag_job_cli --store-id "${label}"\npython -m app.emag_job_cli --store-id "${label}" --from-latest`}</pre><p>第一条只读采集后生成比较、报告和回执；第二条离线重放。未选择店铺时请替换 YOUR_STORE_ID。不注册定时任务，无需保持 console 或模型开启。</p></section>
    <section className="cap-section"><h3>提供给外部 Agent 的 MCP 工具</h3><ul><li><code>ivyea_store_snapshot</code> · read · 读取最近导入的证据</li><li><code>ivyea_emag_job_status</code> · read · 读取最近手动巡检回执</li><li><code>ivyea_report_read</code> · read · 按报告 ID 读取已保存报告</li><li><code>ivyea_report_save</code> · write · 只保存绑定版本的本地报告，不操作平台</li></ul><p>需另外配置本机 MCP 地址和对应令牌；打开本页不代表已连接外部 Agent。没有暴露 eMAG 账号密码、自动改价或上架工具。</p></section>
    <p>社区技能、通用智能体和原平台连接器保留在其他标签。安装技能不会自动获得 eMAG 数据或写入权限。</p>
  </div>;
}
