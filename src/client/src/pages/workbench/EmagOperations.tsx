import { useEffect, useState, useRef } from 'react';
import { api } from '../../api/client';
import { errText } from '../../lib/errText';
import { useSearchParams } from 'react-router-dom';
import { filterIssues, issueForLink, storeForLink } from './emagIssueFilter.mjs';

type Subject = { id:number|string; part_number?:string; reason:string; sale_price?:number|string|null; currency?:string|null; general_stock?:number|null; platform_status?:unknown };
type Entry = { issue_id:string; id:number|string; reason:string; subject?:Subject; platform_status?:unknown; part_number?:string; part_number_key?:string; name?:string; sale_price?:number|string|null; currency?:string|null; general_stock:number|null; state:string; revision:number; history:{state:string;note:string;actor:string;at:string}[] };
type Board = {store_id:string;snapshot_id:string;captured_at:string;source:string;coverage:string[];limitations:string[];summary:Record<string,unknown>;commercial_summary?:{orders_fbe_count:number;orders_seller_count:number;returns_fbe_count:number;returns_seller_count:number;invoice_count:number;invoice_amount_unknown:number;window:{start:string;end:string};inventory:{general_stock_total:number|null;aging_total:number|null;stock_rows_unknown:number;aging_rows_unknown:number;mismatched_skus:number;aging_bands:Record<string,number>};invoice_totals:{category:string;currency:string;amount_as_reported:string}[]};issues:Entry[];records:(Entry & {snapshot_id:string;review_snapshot_id?:string;issue_still_present?:boolean})[]};
const labels:Record<string,string>={pending:'待核实',proposed:'已拟方案',approved:'已批准',executed:'已执行（人工记录）',reviewed:'已复查',invalid_price:'价格无效',documentation_rejected:'资料拒绝',blocked:'平台封锁'};
const next:Record<string,string>={pending:'proposed',proposed:'approved',approved:'executed',executed:'reviewed'};

function platformMessages(status:unknown):string[] {
  const entries=Array.isArray(status)?status:[status];
  return entries.flatMap(entry=>{
    if(!entry||typeof entry!=='object')return [];
    const value=entry as {errors?:unknown;error_details?:unknown};
    const details=Array.isArray(value.error_details)?value.error_details:[];
    const messages=details.flatMap((detail:unknown)=>{
      if(!detail||typeof detail!=='object')return [];
      const item=detail as {message?:unknown;extra_info?:unknown};
      const parts=[item.message,item.extra_info].filter((x):x is string=>typeof x==='string'&&!!x.trim());
      return parts.length?[parts.join(' · ')]:[];
    });
    return messages.length?messages:typeof value.errors==='string'?[value.errors]:[];
  });
}

export default function EmagOperations(){
  const [params,setParams]=useSearchParams();
  const requestedStore=params.get('store');
  const requestedIssue=params.get('issue');
  const request=useRef(0);
  const openedLink=useRef('');
  const [stores,setStores]=useState<{store_id:string}[]>([]),[store,setStore]=useState('');
  const [board,setBoard]=useState<Board|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [selected,setSelected]=useState<(Entry & {snapshot_id?:string})|null>(null),[note,setNote]=useState('');
  const [search,setSearch]=useState(''),[reason,setReason]=useState('all'),[stock,setStock]=useState('all'),[state,setState]=useState('all');
  const context=useRef('');
  context.current=JSON.stringify([store,requestedStore,requestedIssue]);
  useEffect(()=>{let alive=true;api.get('/emag/stores').then(r=>{if(!alive)return;setStores(r.data);const chosen=storeForLink(r.data,requestedStore,requestedIssue);setStore(chosen||'');if(!chosen&&(requestedStore||requestedIssue))setError('指定的店铺不可用，请重新选择。');else setError('');}).catch(()=>{if(alive)setError('无法读取店铺，请确认管理员权限。');});return()=>{alive=false;};},[requestedStore,requestedIssue]);
  async function load(){if(!store)return;const version=++request.current;setSelected(null);setNote('');setError('');setBoard(null);try{const result=await api.get(`/emag/stores/${encodeURIComponent(store)}`);if(version===request.current)setBoard(result.data);}catch{if(version===request.current)setError('读取失败，请重试。');}}
  useEffect(()=>{setSelected(null);if(!store){request.current++;setBoard(null);return;}void load();},[store]);
  useEffect(()=>{if(!requestedIssue){openedLink.current='';return;}if(!board||!requestedStore||board.store_id!==requestedStore)return;const key=`${board.store_id}/${board.snapshot_id}/${requestedIssue}`;if(openedLink.current===key)return;openedLink.current=key;const item=issueForLink(board.issues,requestedIssue);if(item){setSelected({...item,snapshot_id:board.snapshot_id});setNote('');}},[board,requestedIssue,requestedStore]);
  async function save(){if(!selected||!board||board.store_id!==store||(requestedStore&&board.store_id!==requestedStore)||(requestedIssue&&(!requestedStore||selected.issue_id!==requestedIssue)))return;const savedContext=context.current;setBusy(true);setError('');try{await api.post(`/emag/stores/${encodeURIComponent(store)}/issues/${selected.issue_id}`,{snapshot_id:selected.snapshot_id,review_snapshot_id:board.snapshot_id,state:next[selected.state],revision:selected.revision,note});if(context.current===savedContext){setSelected(null);setNote('');await load();}}catch(e:any){if(context.current===savedContext)setError(errText(e,'保存失败，请重新读取后重试。'));}finally{setBusy(false);}}
  function clearIssueLink(){if(requestedIssue)setParams(prev=>{const updated=new URLSearchParams(prev);updated.delete('issue');return updated;});}
  const boardIsCurrent=!!board&&board.store_id===store&&(!requestedStore||board.store_id===requestedStore)&&(!requestedIssue||!!requestedStore);
  const visible=board?filterIssues(board.issues,{search,reason,stock,state}):[];
  const selectedStatus=selected?.platform_status??selected?.subject?.platform_status;
  const messages=platformMessages(selectedStatus);
  return <div style={{padding:24,maxWidth:1400,margin:'auto',fontFamily:'system-ui,sans-serif',fontSize:14,lineHeight:1.6}}>
    <h1>eMAG 店铺巡检</h1><p>从商品异常到人工处理、再用新快照复查。</p>
    <div style={{display:'flex',gap:12,alignItems:'center',flexWrap:'wrap'}}><label>店铺 <select aria-label="店铺" disabled={busy} value={store} onChange={e=>{const value=e.target.value;setStore(value);setParams(prev=>{const updated=new URLSearchParams(prev);updated.set('store',value);updated.delete('issue');return updated;});}}><option value="" disabled>请选择店铺</option>{stores.map(s=><option key={s.store_id}>{s.store_id}</option>)}</select></label><button className="tbtn" disabled={busy||!store} onClick={()=>void load()}>重新读取已采集资料</button></div>
    {error&&<p role="alert">{error}</p>}{!stores.length&&!error&&<p>暂无商品快照。完成 eMAG 只读采集后即可在这里查看。</p>}
    {board&&boardIsCurrent&&<><p>采集时间：{new Date(board.captured_at).toLocaleString()} · 商品记录：{String(board.summary.offers)} · 价格无效：{String(board.summary.invalid_price)} · 有库存且价格无效：{String(board.summary.invalid_price_with_stock)}</p>
      <details><summary>证据范围与限制</summary><p>版本：{board.snapshot_id}</p><p>来源：{board.source}</p><ul>{board.limitations.map(x=><li key={x}>{x}</li>)}</ul></details>
      {board.commercial_summary ? <section aria-label="经营证据"><h2>订单、退货与费用证据</h2><p>订单筛选窗口：{board.commercial_summary.window.start} — {board.commercial_summary.window.end}（平台时区尚未核实）</p><p>FBE 订单 {board.commercial_summary.orders_fbe_count} · 自发货订单 {board.commercial_summary.orders_seller_count} · FBE 退货申请 {board.commercial_summary.returns_fbe_count} · 自发货退货申请 {board.commercial_summary.returns_seller_count} · 费用/折扣单据 {board.commercial_summary.invoice_count}</p><p>已验证总库存字段小计 {board.commercial_summary.inventory.general_stock_total??'未知'} · 已验证库龄分段小计 {board.commercial_summary.inventory.aging_total??'未知'} · 不一致 SKU {board.commercial_summary.inventory.mismatched_skus} · 超过365天的库龄数量 {board.commercial_summary.inventory.aging_bands['365+'] ?? '未知'}</p><p>库存字段未知 {board.commercial_summary.inventory.stock_rows_unknown??'未核实'} 条 · 库龄字段未知 {board.commercial_summary.inventory.aging_rows_unknown??'未核实'} 条 · 费用金额未知 {board.commercial_summary.invoice_amount_unknown??'未核实'} 张。存在未知时，下列金额和库存仅为已验证部分。</p><details><summary>已验证金额按原始符号汇总（不是利润）</summary><ul>{board.commercial_summary.invoice_totals.map(x=><li key={x.category+x.currency}>{x.category}: {x.amount_as_reported} {x.currency}</li>)}</ul></details><p>采购成本待补，尚未计算利润或推荐售价。预留/在途库存未核实。发票日期不等于服务期间，不与订单金额直接相减；退货申请不等于已退款。</p></section> : <p>订单、退款、费用和独立 FBE 库存明细：未采集。</p>}<p>此页面保存本地处理记录；批准不会自动改价或提交商品。</p>
      {requestedIssue&&requestedStore===board.store_id&&!issueForLink(board.issues,requestedIssue)&&<p role="alert">指定异常不在当前快照中，请重新核对商品和快照。</p>}
      <section aria-label="异常筛选"><h2>商品异常</h2><div style={{display:'flex',gap:12,flexWrap:'wrap'}}><label>搜索商品 <input aria-label="搜索异常商品" value={search} onChange={e=>setSearch(e.target.value)} placeholder="商品 / SKU / PNK" /></label><label>异常类型 <select aria-label="异常类型" value={reason} onChange={e=>setReason(e.target.value)}><option value="all">全部</option><option value="invalid_price">价格无效</option><option value="documentation_rejected">资料拒绝</option><option value="blocked">平台封锁</option></select></label><label>库存 <select aria-label="库存筛选" value={stock} onChange={e=>setStock(e.target.value)}><option value="all">全部</option><option value="positive">有库存</option><option value="zero">零库存</option><option value="unknown">未知</option></select></label><label>进度 <select aria-label="处理进度" value={state} onChange={e=>setState(e.target.value)}><option value="all">全部</option>{Object.entries(labels).filter(([key])=>Object.keys(next).includes(key)||key==='reviewed').map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label></div><p>显示 {visible.length} / {board.issues.length} 条异常记录；未知库存不计为零。</p></section>
      <div style={{overflowX:'auto'}}><table style={{width:'100%',borderCollapse:'collapse'}}><thead><tr>{['商品 / SKU','异常','库存字段','进度','操作'].map(x=><th key={x} style={{textAlign:'left',padding:12}}>{x}</th>)}</tr></thead><tbody>{visible.map((i:Entry)=><tr key={i.issue_id}><td style={{padding:12,maxWidth:500}}>{i.name||i.id}<br/><small>{i.part_number||i.id}</small></td><td>{labels[i.reason]||i.reason}</td><td>{i.general_stock??'未知'}</td><td>{labels[i.state]||i.state}</td><td><button className="tbtn" onClick={()=>{clearIssueLink();setSelected({...i,snapshot_id:board.snapshot_id});setNote('');}}>查看 / 记录</button></td></tr>)}</tbody></table></div>
      {board.issues.length>0&&!visible.length&&<p>没有符合当前筛选条件的异常。</p>}
      {!board.issues.length&&<p>当前快照未观察到价格无效、资料拒绝或 Blocked 标记；不代表所有经营风险已排除。</p>}
      <h2>处理记录（最多 100 条）</h2>{board.records.map(r=><div key={r.snapshot_id+r.issue_id} style={{padding:'12px 0'}}><strong>{r.subject?.part_number||r.subject?.id||r.issue_id} · {labels[r.subject?.reason||'']||''} · {labels[r.state]}</strong> · {r.snapshot_id}<p>{r.history.at(-1)?.note}</p>{r.review_snapshot_id&&<p>复查版本：{r.review_snapshot_id} · 异常{r.issue_still_present?'仍存在':'本次未观察到'}</p>}{r.state==='executed'&&r.snapshot_id!==board.snapshot_id&&<button className="tbtn" onClick={()=>{clearIssueLink();setSelected(r);setNote('');}}>用当前快照记录复查</button>}</div>)}
      {selected&&(!requestedIssue||selected.issue_id===requestedIssue)&&<section aria-label="处理记录" style={{padding:20,border:'1px solid currentColor',marginTop:20}}>
        <h2>{selected.name||selected.part_number||selected.subject?.part_number||selected.subject?.id||selected.id||selected.issue_id}</h2>
        <p>SKU：{selected.part_number||selected.subject?.part_number||'未知'} · 商品 ID：{selected.id??selected.subject?.id??'未知'} · 异常：{labels[selected.reason||selected.subject?.reason||'']||selected.reason||selected.subject?.reason||'未知'}</p>
        <p>售价字段：{selected.sale_price??selected.subject?.sale_price??'未知'} {selected.currency??selected.subject?.currency??''} · 库存字段：{selected.general_stock??selected.subject?.general_stock??'未知'}</p>
        <p>来源快照：{selected.snapshot_id} · {selected.snapshot_id===board.snapshot_id?`采集时间：${new Date(board.captured_at).toLocaleString()}`:'历史快照的采集时间未在当前视图加载'}</p>
        <h3>核对步骤</h3>{(selected.reason||selected.subject?.reason)==='invalid_price'&&<p>核对平台价格提示、当前售价、采购成本和费用。成本未补齐前不要推算建议售价；确认价格后再决定是否在平台验证。</p>}{(selected.reason||selected.subject?.reason)==='documentation_rejected'&&<p>按平台审核说明核对商品属性、标题、分类和图片；不清楚的字段请结合实际商品资料确认。</p>}{(selected.reason||selected.subject?.reason)==='blocked'&&<p>当前证据可能没有具体受阻原因，请到平台后台核实状态与原因。</p>}
        <h3>平台审核说明</h3>{messages.length?<ul>{messages.map((message,index)=><li key={index}>{message}</li>)}</ul>:<p>当前快照未提供具体说明，请核对平台后台。</p>}
        <details><summary>查看原始平台状态</summary><pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(selectedStatus??null,null,2)}</pre></details>
        <p>当前：{labels[selected.state]}。下一步：{labels[next[selected.state]]||'流程已结束'}。</p><p>方案请写明字段、旧值、新值与理由；执行记录请注明实际人工操作。复查不等于问题已解决。</p>
        <h3>此异常的处理记录</h3>{selected.history.length?selected.history.map((h,i)=><p key={i}>{labels[h.state]||h.state} · {h.note} · {h.actor} · {h.at}</p>):<p>尚无本地处理记录。</p>}
        <textarea aria-label="处理说明" rows={5} maxLength={4000} value={note} onChange={e=>setNote(e.target.value)} style={{width:'100%'}}/><div style={{display:'flex',gap:12,marginTop:12}}><button className="tbtn" disabled={busy||!note.trim()||!next[selected.state]} onClick={()=>void save()}>保存本地记录</button><button className="tbtn" onClick={()=>{clearIssueLink();setSelected(null);}}>关闭</button></div>
      </section>}
    </>}
  </div>;
}
