"""Local manual operations ledger. Never calls a marketplace."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from app.services import store_artifacts as artifacts
from app.services.emag_readonly import summarize

STATES = ('pending', 'proposed', 'approved', 'executed', 'reviewed')


@contextmanager
def _connect():
    from app.core.config import settings
    root = settings.data_dir
    root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(root / 'emag-operations.sqlite3', timeout=15)
    conn.execute('CREATE TABLE IF NOT EXISTS records (store TEXT, snapshot TEXT, issue TEXT, payload TEXT, PRIMARY KEY(store,snapshot,issue))')
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def stores():
    root = artifacts._root() / 'snapshots'
    result = []
    for directory in sorted(root.iterdir()) if root.exists() else []:
        if directory.is_dir():
            try:
                snapshot = artifacts.read_snapshot(directory.name)
                if snapshot['platform']=='emag' and snapshot['marketplace']=='RO' and isinstance(snapshot['data'].get('offers'), list):
                    result.append({'store_id':directory.name,'captured_at':snapshot['captured_at']})
            except (OSError, ValueError):
                continue
    return result


def _issues(snapshot):
    if snapshot['platform'] != 'emag' or snapshot['marketplace'] != 'RO':
        raise ValueError('An eMAG RO offer snapshot is required')
    rows = snapshot['data'].get('offers')
    if not isinstance(rows, list):
        raise ValueError('Snapshot does not contain offers')
    ids=[str(r['id']) for r in rows if isinstance(r,dict) and type(r.get('id')) in (int,str) and str(r['id']).strip()]
    if len(ids)!=len(rows) or len(set(ids))!=len(ids):
        raise ValueError('Offer snapshot requires unique product IDs')
    result = []
    for issue in summarize(rows)['issues']:
        row = next(r for r in rows if r.get('id') == issue['id'])
        for reason in issue['reasons']:
            key = hashlib.sha256(json.dumps([issue['id'],reason]).encode()).hexdigest()[:24]
            result.append({**issue,'issue_id':key,'reason':reason,'name':row.get('name'),
                           'sale_price':row.get('sale_price'),'currency':row.get('currency'),
                           'platform_status':row.get('offer_validation_status') if reason=='invalid_price' else row.get('validation_status')})
    return sorted(result, key=lambda i: (not(i['reason']=='invalid_price' and (i.get('general_stock') or 0)>0),str(i['id'])))


def board(store_id):
    snapshot = artifacts.read_snapshot(store_id)
    issues = _issues(snapshot)
    with _connect() as conn:
        for issue in issues:
            saved = conn.execute('SELECT payload FROM records WHERE store=? AND snapshot=? AND issue=?',
                                 (store_id,snapshot['snapshot_id'],issue['issue_id'])).fetchone()
            issue.update(json.loads(saved[0]) if saved else {'state':'pending','revision':0,'history':[]})
        history = [json.loads(r[0]) | {'snapshot_id':r[1],'issue_id':r[2]} for r in conn.execute(
            'SELECT payload,snapshot,issue FROM records WHERE store=? ORDER BY rowid DESC LIMIT 100',(store_id,))]
    return {'store_id':store_id,'snapshot_id':snapshot['snapshot_id'],'captured_at':snapshot['captured_at'],
            'source':snapshot['source'],'coverage':snapshot['coverage'],'limitations':snapshot['limitations'],
            'summary':summarize(snapshot['data']['offers']),'issues':issues,'records':history}


def transition(store_id, snapshot_id, issue_id, state, revision, note, actor, review_snapshot_id=None):
    if state not in STATES[1:] or not note.strip() or len(note)>4000:
        raise ValueError('A valid state and a note of 1–4000 characters are required')
    original=artifacts.read_snapshot(store_id,snapshot_id)
    subject=next((i for i in _issues(original) if i['issue_id']==issue_id), None)
    if subject is None:
        raise ValueError('Issue does not belong to this snapshot')
    with artifacts.snapshot_guard(), _connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        latest=artifacts.read_snapshot(store_id)
        row=conn.execute('SELECT payload FROM records WHERE store=? AND snapshot=? AND issue=?',(store_id,snapshot_id,issue_id)).fetchone()
        current=json.loads(row[0]) if row else {'state':'pending','revision':0,'history':[]}
        if current['revision']!=revision or STATES.index(state)!=STATES.index(current['state'])+1:
            raise ValueError('Record changed or transition is out of order; reload first')
        if state!='reviewed' and latest['snapshot_id']!=snapshot_id:
            raise ValueError('Evidence is stale; use the latest snapshot')
        if state=='reviewed':
            if latest['snapshot_id']==snapshot_id or latest['snapshot_id']!=review_snapshot_id:
                raise ValueError('Review requires the explicitly inspected newer latest snapshot; reload first')
            current.update(review_snapshot_id=latest['snapshot_id'],
                           issue_still_present=issue_id in {i['issue_id'] for i in _issues(latest)})
        current.update(state=state,revision=revision+1,subject=subject)
        current['history'].append({'state':state,'note':note.strip(),'actor':actor,'at':datetime.now(timezone.utc).isoformat()})
        conn.execute('INSERT OR REPLACE INTO records VALUES (?,?,?,?)',(store_id,snapshot_id,issue_id,json.dumps(current)))
    return {'issue_id':issue_id,**current}
