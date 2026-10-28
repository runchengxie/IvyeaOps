import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';

type Offer={id:string|number;name?:string;part_number?:string;part_number_key?:string;sale_price?:number|string;general_stock?:number|null;category_id?:number;brand?:string};
type Draft={draft_id:string;kind:string;title:string;body:string;product_id:string;stale:boolean;created_at:string};
type Evidence={store_id:string;snapshot_id:string;captured_at:string;source:string;coverage:string[];limitations:string[];offers:Offer[];summary:Record<string,unknown>;issues:{issue_id:string;reason:string;id:string|number;general_stock:number|null}[];drafts:Draft[];commercial_summary?:{orders_fbe_count:number;orders_seller_count:number;invoice_count:number;inventory:{general_stock_total:number|null;aging_total:number|null;mismatched_skus:number}}};
export type WorkspaceMode='dashboard'|'market'|'playbook'|'listing'|'tools';
const titles:Record<WorkspaceMode,string>={dashboard:'运营驾驶舱',market:'市场调研',playbook:'打法推荐',listing:'Listing 工作台',tools:'分析工具'};

export default function EmagWorkspace({mode}:{mode:WorkspaceMode}){
  const [stores,setStores]=useState<{store_id:string}[]>([]),[store,setStore]=useState('');
  const [data,setData]=useState<Evidence|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [search,setSearch]=useState(''),[product,setProduct]=useState(''),[title,setTitle]=useState(''),[body,setBody]=useState('');
  const [job,setJob]=useState<Record<string,unknown>|null>(null);
  const generation=useRef(0);
  useEffect(()=>{api.get('/emag/stores').then(r=>{setStores(r.data);if(r.data.length)setStore(r.data[0].store_id);}).catch(()=>setError('读取失败，需要管理员权限。'));},[]);
  async function load(){if(!store)return;const version=++generation.current;setData(null);setJob(null);setProduct('');setTitle('');setBody('');setError('');try{const r=await api.get(`/emag/stores/${encodeURIComponent(store)}/workspace`);if(version!==generation.current)return;setData(r.data);const j=await api.get(`/emag/stores/${encodeURIComponent(store)}/job`).catch(()=>null);if(version===generation.current)setJob(j?.data||null);}catch{if(version===generation.current)setError('无法读取 eMAG 快照，请先完成只读采集。');}}
  useEffect(()=>{void load();return()=>{generation.current++;};},[store]);
  const kind=mode==='listing'?'listing':mode==='playbook'?'playbook':'research';
  async function save(){if(!data)return;setBusy(true);setError('');try{await api.post(`/emag/stores/${encodeURIComponent(store)}/drafts`,{snapshot_id:data.snapshot_id,kind,product_id:product,title,body});await load();}catch(e:any){setError(e.response?.data?.detail||'保存失败');}finally{setBusy(false);}}
  const offers=data?.offers.filter(o=>`${o.name||''} ${o.part_number||''} ${o.part_number_key||''} ${o.id}`.toLowerCase().includes(search.toLowerCase()))||[];
  const categories=new Map<string,number>();data?.offers.forEach(o=>{const key=String(o.category_id??'未知');categories.set(key,(categories.get(key)||0)+1);});
  return <main style={{padding:24,maxWidth:1400,margin:'auto',fontFamily:'system-ui,sans-serif',fontSize:14,lineHeight:1.7,minWidth:0,overflowWrap:'anywhere'}}>
    <h1>eMAG {titles[mode]}</h1><p>RO · RON · 商品 ID / SKU / PNK · 已采集证据</p>
    <nav style={{display:'flex',gap:14,flexWrap:'wrap'}}>{Object.entries(titles).map(([key,label])=><Link key={key} to={`/${key}`}>{label}</Link>)}<Link to="/emag">巡检处理记录</Link></nav>
    <p><label>店铺 <select aria-label="店铺" value={store} disabled={busy} onChange={e=>setStore(e.target.value)}>{stores.map(s=><option key={s.store_id}>{s.store_id}</option>)}</select></label> <button className="tbtn" disabled={busy} onClick={()=>void load()}>重新读取资料</button></p>
    {error&&<p role="alert">{error}</p>}{!stores.length&&!error&&<p>暂无 eMAG RO 快照。请先通过手动无头命令采集。</p>}
    {data&&<><p>采集时间 {new Date(data.captured_at).toLocaleString()} · {data.offers.length} 条商品 · 异常原因 {data.issues.length} 项</p>
      <details><summary>来源、版本与限制</summary><p>{data.source} · {data.snapshot_id}</p><p>覆盖：{data.coverage.join('、')}</p><ul>{data.limitations.map((x,i)=><li key={i}>{x}</li>)}</ul></details>
      {mode==='dashboard'&&<section><h2>经营证据</h2>{data.commercial_summary?<p>FBE 订单 {data.commercial_summary.orders_fbe_count} · 自发货订单 {data.commercial_summary.orders_seller_count} · 单据 {data.commercial_summary.invoice_count} · 库存已知字段小计 {data.commercial_summary.inventory.general_stock_total??'未知'} · 库龄字段小计 {data.commercial_summary.inventory.aging_total??'未知'} · 库存差异 SKU {data.commercial_summary.inventory.mismatched_skus}</p>:<p>订单、退货、费用明细未采集。</p>}<p>采购成本待补，利润与推荐售价暂不计算。订单数量不代表成交金额，费用单据日期不代表服务期间。</p><Link to="/emag">查看费用分类、未知字段和处理进度</Link></section>}
      {mode==='market'&&<section><h2>本店商品结构</h2><p>按平台 category_id 统计，不代表市场需求或竞品份额。全市场搜索量、竞品价格与销量尚未接入。</p><ul>{[...categories].sort((a,b)=>b[1]-a[1]).map(([c,n])=><li key={c}>类目 {c}：{n} 条</li>)}</ul><p>可在下方保存有来源链接、采集日期和观察范围的人工调研记录。</p></section>}
      {mode==='playbook'&&<section><h2>依据现有异常安排动作</h2><ol><li>优先核实有库存且价格无效的商品：{data.issues.filter(i=>i.reason==='invalid_price'&&(i.general_stock??0)>0).length} 条。</li><li>资料拒绝与封锁逐项核对平台原因，补齐凭证后人工处理。</li><li>补齐采购成本、运费与税费后再评估售价，复查必须采集新快照。</li></ol><p>此处保存方案草稿；审批与人工执行记录在巡检页逐步填写。</p></section>}
      {mode==='tools'&&<section><h2>资料质量与巡检回执</h2><p>库存未知 {data.offers.filter(o=>o.general_stock==null).length} 条 · 标题缺失 {data.offers.filter(o=>!o.name?.trim()).length} 条 · 售价缺失 {data.offers.filter(o=>o.sale_price==null).length} 条。</p>{job?<><p>最近任务：{String(job.status)} · {String(job.mode)} · 阶段 {String(job.stage)}</p><p>回执版本：{String(job.snapshot_id||'未生成')} · {job.snapshot_id===data.snapshot_id?'与当前资料一致':'与当前资料不同'}</p><details><summary>增量与报告引用</summary><pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(job,null,2)}</pre></details></>:<p>尚无手动巡检回执。离线重放不会重新采集，也不产生新旧变化结论。</p>}</section>}
      <h2>{mode==='listing'?'选择商品，起草罗马尼亚语内容':'本店商品明细'}</h2><input aria-label="搜索商品" placeholder="搜索标题 / SKU / PNK" value={search} onChange={e=>setSearch(e.target.value)} style={{maxWidth:'100%',width:400}}/>
      <div style={{overflowX:'auto'}}><table style={{width:'100%',minWidth:620,textAlign:'left'}}><thead><tr><th>商品 / SKU / PNK</th><th>售价字段</th><th>库存字段</th>{mode==='listing'&&<th>草稿</th>}</tr></thead><tbody>{offers.slice(0,500).map(o=><tr key={o.id}><td style={{padding:'10px 0',minWidth:190}}>{o.name||'标题未知'}<br/><small>{o.part_number||o.id} · {o.part_number_key||'PNK 未采集'}</small></td><td>{o.sale_price??'未知'}</td><td>{o.general_stock??'未知'}</td>{mode==='listing'&&<td><button className="tbtn" disabled={busy} onClick={()=>{setProduct(String(o.id));setTitle(o.name||'');setBody('');}}>起草</button></td>}</tr>)}</tbody></table></div>{offers.length>500&&<p>仅展示前 500 条，请缩小搜索范围。</p>}
      {['listing','market','playbook'].includes(mode)&&<section style={{border:'1px solid var(--border)',padding:16,marginTop:20}}><h2>{mode==='listing'?'本地 Listing 草稿':'本地工作记录'}</h2><p>{product?`商品 ID：${product}`:'全店记录'} · 绑定当前证据版本。保存不会提交 eMAG。规格、认证和卖点须有依据；未接入自动生成模型。</p><label>标题<input aria-label="草稿标题" maxLength={200} value={title} onChange={e=>setTitle(e.target.value)} style={{display:'block',width:'100%'}}/></label><label>内容<textarea aria-label="草稿内容" rows={7} maxLength={40000} value={body} onChange={e=>setBody(e.target.value)} style={{display:'block',width:'100%'}}/></label><button className="tbtn" disabled={busy||!title.trim()||!body.trim()||(mode==='listing'&&!product)} onClick={()=>void save()}>保存本地草稿</button><h3>已保存记录</h3>{data.drafts.filter(d=>d.kind===kind).map(d=><details key={d.draft_id}><summary>{d.title} · {d.stale?'来源已更新，请重新核对':'当前来源'} · {new Date(d.created_at).toLocaleString()}</summary><p>商品：{d.product_id||'全店'}</p><pre style={{whiteSpace:'pre-wrap'}}>{d.body}</pre></details>)}</section>}
    </>}
  </main>;
}
