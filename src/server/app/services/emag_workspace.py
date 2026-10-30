"""Snapshot-bound local drafts; never publishes a marketplace listing."""
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from app.services import store_artifacts as artifacts, emag_operations


@contextmanager
def _db():
    from app.core.config import settings
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.data_dir / 'emag-workspace.sqlite3')
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS drafts (id TEXT PRIMARY KEY, store TEXT, payload TEXT)')
        with conn:
            yield conn
    finally:
        conn.close()


def view(store_id):
    board = emag_operations.board(store_id)
    snapshot = artifacts.read_snapshot(store_id, board['snapshot_id'])
    with _db() as conn:
        drafts = [json.loads(row[0]) for row in conn.execute(
            'SELECT payload FROM drafts WHERE store=? ORDER BY rowid DESC LIMIT 100', (store_id,))]
    for draft in drafts:
        draft['stale'] = draft['snapshot_id'] != snapshot['snapshot_id']
    from app.services import emag_quality
    return {**board, 'offers': snapshot['data']['offers'], 'drafts': drafts, 'return_voc':emag_quality.return_voc(snapshot)}


def save_draft(store_id, snapshot_id, kind, product_id, title, body, actor):
    if kind not in ('listing', 'research', 'playbook'):
        raise ValueError('Unknown draft kind')
    if not title.strip() or len(title) > 200 or not body.strip() or len(body) > 40000:
        raise ValueError('Title/body required (maximum 200/40000 characters)')
    with artifacts.snapshot_guard():
        snapshot = artifacts.read_snapshot(store_id)
        emag_operations._issues(snapshot)
        if snapshot['snapshot_id'] != snapshot_id:
            raise ValueError('Evidence is stale; reload first')
        if kind == 'listing' or product_id:
            if not any(str(row['id']) == product_id for row in snapshot['data']['offers']):
                raise ValueError('Select a product from the source snapshot')
        draft = {'draft_id': secrets.token_hex(16), 'store_id': store_id, 'snapshot_id': snapshot_id,
                     'kind': kind, 'product_id': product_id, 'title': title.strip(), 'body': body.strip(),
                     'actor': actor, 'created_at': datetime.now(timezone.utc).isoformat()}
        if kind=='listing':
            from app.services import emag_quality
            offer=next(row for row in snapshot['data']['offers'] if str(row['id'])==product_id)
            draft['quality_check']=emag_quality.listing_check(title,body,offer)
        with _db() as conn:
            conn.execute('INSERT INTO drafts VALUES (?,?,?)', (draft['draft_id'],store_id,json.dumps(draft)))
    return draft
