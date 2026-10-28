import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import { useAuth } from '../../App';

type Issue={issue_id:string;id:string|number;name?:string;part_number?:string;reason:string;general_stock:number|null;sale_price?:string|number;platform_status?:unknown;state:string;revision:number;history:{state:string;note:string;actor:string;at:string}[]};
type Board={store_id:string;snapshot_id:string;captured_at:string;source:string;issues:Issue[];records:{state:string;snapshot_id:string}[]};
type Proposal={board:Board;issue:Issue};
const reasons:Record<string,string>={invalid_price:'价格无效',documentation_rejected:'资料拒绝',blocked:'平台封锁'};
const key=(p:Proposal)=>`${p.board.store_id}/${p.board.snapshot_id}/${p.issue.issue_id}`;

export default function EmagApprovalQueue(){
  const {role}=useAuth();
  const generation=useRef(0);
  const [boards,setBoards]=useState<Board[]|null>(null),[error,setError]=useState('');
  const [failed,setFailed]=useState<string[]>([]),[selected,setSelected]=useState<Proposal|null>(null);
  const [note,setNote]=useState(''),[busy,setBusy]=useState(false),[stale,setStale]=useState(false);
  const load=useCallback(async()=>{
    if(role!=='admin')return;
    const version=++generation.current;
    setBoards(null);setSelected(null);setNote('');setError('');setFailed([]);setStale(false);
    try{
      const {data:stores}=await api.get<{store_id:string}[]>('/emag/stores');
      if(version!==generation.current)return;
      const results=await Promise.allSettled(stores.map(s=>api.get<Board>(`/emag/stores/${encodeURIComponent(s.store_id)}`)));
      if(version!==generation.current)return;
      setBoards(results.flatMap(r=>r.status==='fulfilled'?[r.value.data]:[]));
      setFailed(stores.filter((_,i)=>results[i].status==='rejected').map(s=>s.store_id));
    }catch{if(version===generation.current)setError('eMAG 来源读取失败，无法判断待批数量。');}
  },[role]);
  useEffect(()=>{void load();return()=>{generation.current++;};},[load]);
  if(role!=='admin')return <section style={{padding:16}}><h2>eMAG 本地方案待审批</h2><p>此队列由管理员查看与处理；不会读取店铺资料。</p></section>;
  const proposals=boards?.flatMap(board=>board.issues.filter(i=>i.state==='proposed').map(issue=>({board,issue})))||[];
  const old=boards?.reduce((n,b)=>n+b.records.filter(r=>r.state==='proposed'&&r.snapshot_id!==b.snapshot_id).length,0)||0;
  async function approve(){
    if(!selected||!note.trim()||stale||busy)return;
    setBusy(true);setError('');
    try{
      await api.post(`/emag/stores/${encodeURIComponent(selected.board.store_id)}/issues/${encodeURIComponent(selected.issue.issue_id)}`,{
        snapshot_id:selected.board.snapshot_id,state:'approved',revision:selected.issue.revision,note,
      });
      await load();
    }catch(e:any){
      if(e.response?.status===409){setStale(true);setError('资料版本或处理记录已变化，请重新读取并核对后再批准。');}
      else setError('未能确认批准结果。请重新读取记录核实，不要将请求失败视为已批准。');
    }finally{setBusy(false);}
  }
  return <section aria-label="eMAG 本地审批" style={{padding:'18px 16px',fontFamily:'system-ui',lineHeight:1.7,overflowWrap:'anywhere',minWidth:0}}>
    <h2>eMAG 本地方案待审批</h2><p>仅批准当前快照中已拟定的方案，保存后不会改价、上架或处理订单。实际执行与新版本复查仍需另行记录。</p>
    <button className="tbtn" disabled={busy} onClick={()=>void load()}>重新读取 eMAG 待批</button>
    {error&&<p role="alert">{error}</p>}
    {!!failed.length&&<p role="alert">以下店铺读取失败，列表不完整：{failed.join('、')}。未将读取失败视为没有待批事项。</p>}
    {boards===null&&!error&&<p>正在读取 eMAG 方案…</p>}
    {boards!==null&&<p>成功读取 {boards.length} 个店铺 · 当前待批方案 {proposals.length} 条 · 旧版本已拟方案参考记录 {old} 条（最多读取每店 100 条历史记录，不参与当前批准）。</p>}
    {boards!==null&&!failed.length&&!proposals.length&&<p>当前资料中暂无已拟方案待批准。先在 <Link to="/emag">eMAG 巡检</Link> 核查异常、记录方案；无待批不代表店铺没有问题。</p>}
    {proposals.map(p=>{
      const proposal=p.issue.history.filter(h=>h.state==='proposed').at(-1);
      return <article className="ap-card" key={key(p)}>
        <h3>{p.issue.name||p.issue.part_number||p.issue.id} · {reasons[p.issue.reason]||p.issue.reason}</h3>
        <p>店铺：{p.board.store_id} · 商品 ID：{p.issue.id} · SKU：{p.issue.part_number||'未知'}<br/>库存字段：{p.issue.general_stock??'未知'} · 售价字段：{p.issue.sale_price??'未知'}</p>
        <p>来源：{p.board.source}<br/>采集：{new Date(p.board.captured_at).toLocaleString()}<br/>版本：{p.board.snapshot_id} · revision {p.issue.revision}</p>
        <h4>待批准的方案</h4><p style={{whiteSpace:'pre-wrap'}}>{proposal?.note||'方案说明缺失，请先核对上下文。'}</p>
        {proposal&&<p>提出者：{proposal.actor} · {new Date(proposal.at).toLocaleString()}</p>}
        <details><summary>平台状态证据</summary><pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(p.issue.platform_status??null,null,2)}</pre></details>
        <div style={{display:'flex',gap:12,flexWrap:'wrap'}}><Link to={`/emag?store=${encodeURIComponent(p.board.store_id)}`}>查看店铺完整上下文</Link><button className="tbtn" disabled={busy||stale||!proposal?.note?.trim()} onClick={()=>{setSelected(p);setNote('');}}>核对并批准本地方案</button></div>
      </article>;
    })}
    {selected&&<section aria-label="本地批准确认" style={{padding:16,border:'1px solid var(--b)',marginTop:16}}><h3>核对批准说明</h3><p>{selected.board.store_id} · {selected.issue.part_number||selected.issue.id} · {reasons[selected.issue.reason]||selected.issue.reason}</p><p style={{whiteSpace:'pre-wrap'}}>{selected.issue.history.filter(h=>h.state==='proposed').at(-1)?.note}</p><p>保存只将本地状态从“已拟方案”变为“已批准”。当前流程没有“退回修改”状态；尚未核实的方案请保留待批。</p><label>批准说明<textarea aria-label="批准说明" maxLength={4000} rows={4} value={note} disabled={busy||stale} onChange={e=>setNote(e.target.value)} style={{display:'block',width:'100%'}}/></label><button className="tbtn" disabled={busy||stale||!note.trim()} onClick={()=>void approve()}>确认保存本地批准</button> <button className="tbtn" disabled={busy} onClick={()=>{setSelected(null);setNote('');}}>暂不批准</button></section>}
  </section>;
}
