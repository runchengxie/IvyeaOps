import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../App';
import { api } from '../../api/client';
import { previewCron } from '../../api/schedules';

type Preview={ok:boolean;next?:string[];error?:string;timezone?:string};
type Receipt={status:string;mode:string;stage:string;snapshot_id?:string;finished_at?:string};
export default function EmagSchedulePlan(){
  const {role}=useAuth();
  const [stores,setStores]=useState<{store_id:string}[]|null>(null),[store,setStore]=useState(''),[error,setError]=useState('');
  const [receipt,setReceipt]=useState<Receipt|null>(null),[receiptState,setReceiptState]=useState('');
  const [cron,setCron]=useState('0 9 * * *'),[days,setDays]=useState(29),[offline,setOffline]=useState(false);
  const [preview,setPreview]=useState<Preview|null>(null),[previewBusy,setPreviewBusy]=useState(false);
  const version=useRef(0);
  useEffect(()=>{if(role!=='admin')return;let alive=true;api.get('/emag/stores').then(r=>{if(alive){setStores(r.data);setStore(r.data[0]?.store_id||'');}}).catch(()=>{if(alive)setError('来源读取失败，无法生成店铺计划。');});return()=>{alive=false;};},[role]);
  useEffect(()=>{setReceipt(null);setReceiptState('');if(role!=='admin'||!store)return;let alive=true;setReceiptState('正在读取回执…');api.get(`/emag/stores/${encodeURIComponent(store)}/job`).then(r=>{if(alive){setReceipt(r.data);setReceiptState('');}}).catch(e=>{if(alive)setReceiptState(e.response?.status===404?'暂无手动巡检回执。':'回执读取失败，不能判断最近运行结果。');});return()=>{alive=false;};},[role,store]);
  useEffect(()=>()=>{version.current++;},[]);
  function changeCron(value:string){version.current++;setCron(value);setPreview(null);setPreviewBusy(false);}
  async function calculate(){const current=++version.current;setPreview(null);setPreviewBusy(true);try{const result=await previewCron(cron);if(version.current===current)setPreview(result);}catch{if(version.current===current)setPreview({ok:false,error:'无法读取服务器时间预览，请重试。'});}finally{if(version.current===current)setPreviewBusy(false);}}
  const validStore=/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(store);
  const validDays=Number.isInteger(days)&&days>=1&&days<=29;
  const validWindow=offline||validDays;
  const label=validStore?store:'YOUR_STORE_ID';
  const argv=['-m','app.emag_job_cli','--store-id',label,...(offline?['--from-latest']:['--days',String(days)])];
  function download(){
    if(!validStore||!validWindow||!preview?.ok||!preview.timezone||!preview.next?.length)return;
    const plan={version:1,kind:'emag-readonly-plan',enabled:false,registered:false,scheduler_connected:false,store_id:store,cron,timezone:preview.timezone,mode:offline?'existing_snapshot':'fresh_collection',days:offline?null:days,argv,requires_backend_data_dir:true,preview_times:preview.next};
    const url=URL.createObjectURL(new Blob([JSON.stringify(plan,null,2)],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download=`emag-plan-${store}.json`;a.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  if(role!=='admin')return <section style={{padding:20,lineHeight:1.7}}><h2>eMAG 巡检计划准备</h2><p>当前保持手动运行。管理员可查看店铺回执、预览节奏并导出停用的计划草稿；此处不读取私有店铺资料。</p></section>;
  return <section style={{padding:'16px 20px',lineHeight:1.7,fontFamily:'system-ui',minWidth:0,overflowWrap:'anywhere'}}>
    <h2>eMAG 巡检计划准备</h2><p>当前选择仍为手动运行。此页可预览和下载草稿，不注册操作系统任务、不启用自动调度、不运行采集。确定性的 eMAG CLI 尚未接入通用 Agent 调度器。</p>
    {error&&<p role="alert">{error}</p>}{stores===null&&!error&&<p>正在读取店铺来源…</p>}{stores?.length===0&&<p>暂无本地店铺来源，请先完成手动采集或导入；无法据此判断 API 凭证状态。</p>}
    {!!stores?.length&&<><label>巡检店铺 <select aria-label="巡检店铺" value={store} onChange={e=>setStore(e.target.value)}>{stores.map(s=><option key={s.store_id}>{s.store_id}</option>)}</select></label>
      <h3>最近手动运行</h3>{receipt?<><p>{receipt.status} · {receipt.mode} · 阶段 {receipt.stage}</p><p>完成时间：{receipt.finished_at?new Date(receipt.finished_at).toLocaleString():'未提供'} · 版本 {receipt.snapshot_id||'未生成'}</p><p>这是该次回执，不证明当前最新资料已巡检，也不代表有定时任务在运行。<Link to="/tools">核对当前证据</Link></p></>:<p role="status">{receiptState}</p>}
    </>}
    <h3>准备手动命令</h3><label><input type="checkbox" checked={offline} onChange={e=>setOffline(e.target.checked)}/> 离线重放已有快照（不重新采集）</label>{!offline&&<p><label>采集窗口天数 <input aria-label="采集窗口天数" type="number" min={1} max={29} value={days} onChange={e=>setDays(Number(e.target.value))}/></label> · 1—29 天</p>}
    <pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{`python -m app.emag_job_cli --store-id "${label}" ${offline?'--from-latest':`--days ${validDays?days:'DAYS_1_TO_29'}`}`}</pre><p>在 server 目录使用后端同一 Python 环境、同一 IVYEA_OPS_DATA_DIR。联网模式需要可用的 eMAG 权限和 Windows 普通凭据 IvyeaOps/eMAG/RO；无需打开 console 或模型。此页不读取密码。</p>
    <h3>预览未来运行节奏（未启用）</h3><p>下列每天 09:00 仅为示例草稿，不表示你已选择该频率。预览按服务器时区计算，不自动转换为罗马尼亚时间。</p>
    <label>cron 表达式 <input aria-label="cron 表达式" maxLength={120} value={cron} onChange={e=>changeCron(e.target.value)} style={{maxWidth:'100%'}}/></label> <button className="tbtn" disabled={!cron.trim()||previewBusy} onClick={()=>void calculate()}>预览触发时间</button>
    {previewBusy&&<p>正在计算服务器触发时间…</p>}{preview&&<p role={preview.ok?'status':'alert'}>{preview.ok?`服务器时区：${preview.timezone||'未知'}；预览：${preview.next?.join(' · ')||'未返回时间'}`:`预览失败：${preview.error||'未返回有效结果'}`}</p>}
    <p><button className="tbtn" disabled={!validStore||!validWindow||!preview?.ok||!preview.timezone||!preview.next?.length} onClick={download}>下载停用计划草稿</button></p><p>JSON 草稿固定 enabled=false、registered=false；当前没有导入或执行该草稿的调度器。下载不会保存服务器任务，启用自动运行需后续单独对接。</p>
  </section>;
}
